# One public origin. The listener sends /api/v1/ai/* to ai_api and everything
# else to core_api, so the frontend needs a single NEXT_PUBLIC_API_URL.

resource "aws_lb" "backend" {
  name               = "${var.name_prefix}-backend"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  # Streamed chat answers can take a couple of minutes.
  idle_timeout = 300
}

resource "aws_lb_target_group" "core_api" {
  name        = "${var.name_prefix}-core-api"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/api/v1/health/"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_target_group" "ai_api" {
  name        = "${var.name_prefix}-ai-api"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/api/v1/ai/health/"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.core_api.arn
  }
}

resource "aws_lb_listener_rule" "ai_api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ai_api.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/ai/*"]
    }
  }
}
