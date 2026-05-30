import 'package:flutter/material.dart';

void syncAnimationWithTickerMode(
  BuildContext context,
  AnimationController controller, {
  bool reverse = false,
}) {
  if (TickerMode.of(context)) {
    if (!controller.isAnimating) {
      controller.repeat(reverse: reverse);
    }
    return;
  }

  controller.stop();
}
