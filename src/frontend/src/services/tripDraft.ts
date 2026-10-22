/**
 * A saved trip, back as the planner draft it was saved from: the inverse of `saveDraftAsTrip`.
 * A child with no stored `card` gets one rebuilt from its columns. Pure: no network or storage.
 */

import { EMPTY_ITINERARY, type DayDraft, type PlannerDraft } from "@/hooks/plannerReducer";
import type { DayPart, OptionCard, RouteInfo, TripBrief } from "@/types/planner";
import type { Accommodation, Activity, Meal, PartOfDay, Trip } from "@/types/trip";
import { daysBetween } from "@/utils/tripDates";
import { EAT } from "./trips";

/**
 * Whether the stored JSON is a planner card. Deliberately shallow: an id and a title are what
 * every consumer indexes into; the rest of the card is optional to read.
 */
export function isOptionCard(value: unknown): value is OptionCard {
  if (typeof value !== "object" || value === null) return false;
  const card = value as Record<string, unknown>;
  return typeof card.id === "string" && typeof card.title === "string";
}

/**
 * The card for a child that carries none: everything the columns know, and
 * nothing invented. An empty `source`/`license` is what the planner shows as
 * "no source", which is the truth here.
 */
function cardFromColumns(input: {
  id: string;
  title: string;
  category: string;
  subtitle?: string;
  why?: string;
  lat: number | null;
  lon: number | null;
}): OptionCard {
  return {
    id: input.id,
    title: input.title,
    subtitle: input.subtitle || null,
    district: null,
    category: input.category,
    image_url: null,
    image_credit: null,
    price_tier: null,
    rating_text: null,
    hours: null,
    lat: input.lat,
    lon: input.lon,
    why: input.why ?? "",
    source: "",
    source_url: "",
    license: "",
    deep_link: null,
  };
}

/** The stored card, or one built from the columns beside it. */
function cardOf(
  stored: unknown,
  fallback: Parameters<typeof cardFromColumns>[0]
): OptionCard {
  return isOptionCard(stored) ? stored : cardFromColumns(fallback);
}

/**
 * Which part of the day an hour reads as, for a child without `part_of_day`. The thresholds
 * agree with `PART_TIME` (`services/trips.ts`) and with the column's backfill (ADR 0019).
 */
export function partFromTime(time: string): DayPart {
  const hour = Number(time.slice(0, 2));
  if (!Number.isFinite(hour)) return "morning";
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  if (hour < 21) return "evening";
  return "night";
}

function partOfChild(partOfDay: PartOfDay | null, time: string): DayPart {
  return partOfDay ?? partFromTime(time);
}

function activityCard(activity: Activity): OptionCard {
  return cardOf(activity.card, {
    id: activity.sourceRef || activity.id,
    title: activity.title,
    category: activity.category || "see",
    why: activity.description,
    lat: activity.place.coordinates.lat,
    lon: activity.place.coordinates.lng,
  });
}

function mealCard(meal: Meal): OptionCard {
  return cardOf(meal.card, {
    id: meal.sourceRef || meal.id,
    title: meal.restaurantName,
    category: EAT,
    subtitle: meal.cuisine,
    lat: meal.place.coordinates.lat,
    lon: meal.place.coordinates.lng,
  });
}

function stayCard(stay: Accommodation): OptionCard {
  return cardOf(stay.card, {
    id: stay.sourceRef || stay.id,
    title: stay.name,
    category: "sleep",
    lat: stay.coordinates.lat,
    lon: stay.coordinates.lng,
  });
}

/** The three paces the brief knows; anything else is as good as unset. */
const PACES = ["relaxed", "balanced", "intense"] as const;

function paceOf(pace: string): TripBrief["pace"] {
  return (PACES as readonly string[]).includes(pace) ? (pace as TripBrief["pace"]) : null;
}

/** 1, 2 or 3; anything else never came from the planner. */
function budgetTierOf(tier: number | null): TripBrief["budget_tier"] {
  return tier === 1 || tier === 2 || tier === 3 ? tier : null;
}

/** The brief the trip was planned from, out of the columns it was written to. */
export function tripToBrief(trip: Trip): TripBrief {
  const { startDate, endDate, durationDays } = trip.dates;
  const days = daysBetween(startDate, endDate) ?? durationDays;
  return {
    destination: trip.city.name,
    origin: trip.origin || null,
    start_date: startDate || null,
    end_date: endDate || null,
    nights: days > 0 ? days - 1 : null,
    adults: trip.travellers.adults,
    children: trip.travellers.children,
    budget_tier: budgetTierOf(trip.budgetTier),
    interests: trip.interests,
    pace: paceOf(trip.pace),
  };
}

/** The date part of a stored `date-time`; the route only ever knows days. */
function dayOf(dateTime: string): string | null {
  const date = dateTime.slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(date) ? date : null;
}

/**
 * The route, from the two legs it was saved as. A trip with no outbound leg
 * has no route: the strip would have nowhere to leave from.
 */
function routeOf(trip: Trip): RouteInfo | null {
  const outbound = trip.legs.find((leg) => leg.category === "outbound");
  if (!outbound) return null;
  const back = trip.legs.find((leg) => leg.category === "return");
  return {
    origin: outbound.fromCity,
    destination: outbound.toCity,
    outbound_date: dayOf(outbound.departureTime),
    return_date: back ? dayOf(back.departureTime) : null,
    // the deep link was a one-off search; it is not stored
    deep_link: null,
  };
}

function emptySlots(): Record<DayPart, OptionCard[]> {
  return { morning: [], afternoon: [], evening: [], night: [] };
}

/**
 * One saved day as the planner holds it, each card in the part of the day it was saved with.
 * The weather is not restored: it was a forecast for dates that may have passed.
 */
function dayOfTrip(day: Trip["itinerary"][number]): DayDraft {
  const slots = emptySlots();
  for (const activity of day.activities) {
    slots[partOfChild(activity.partOfDay, activity.time)].push(activityCard(activity));
  }
  for (const meal of day.meals) {
    slots[partOfChild(meal.partOfDay, meal.time)].push(mealCard(meal));
  }
  return { day: day.dayNumber, title: day.title || null, weather: null, slots };
}

export interface TripDraft {
  draft: PlannerDraft;
  /** The trip this draft belongs to: "Save trip" updates it rather than adding one. */
  tripId: string;
}

/**
 * A trip as a planner draft, ready for `usePlanner.hydrate`. The transcript starts empty
 * (core_api stores no chat); the stateless ai_api carries on from the brief and the itinerary.
 */
export function tripToDraft(trip: Trip): TripDraft {
  const days = trip.itinerary.map(dayOfTrip).sort((a, b) => a.day - b.day);
  return {
    tripId: trip.id,
    draft: {
      messages: [],
      groups: {},
      brief: tripToBrief(trip),
      missing: [],
      itinerary: {
        ...EMPTY_ITINERARY,
        stay: trip.stay ? stayCard(trip.stay) : null,
        days,
        route: routeOf(trip),
      },
      shortlist: [],
    },
  };
}
