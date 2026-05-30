import 'package:flutter/material.dart';

import 'skeleton_pulse.dart';

class SkeletonLine extends StatelessWidget {
  const SkeletonLine({
    super.key,
    this.width,
    this.height = 14,
  });

  final double? width;
  final double height;

  @override
  Widget build(BuildContext context) {
    final pulse = SkeletonPulse.animationOf(context);
    final baseColor = Theme.of(context).colorScheme.surfaceContainerHighest;
    final highlightColor = Theme.of(context).colorScheme.surfaceContainerHigh;

    Widget line(Color color) {
      return Container(
        height: height,
        width: width,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(4),
        ),
      );
    }

    if (pulse == null) {
      return line(baseColor);
    }

    return AnimatedBuilder(
      animation: pulse,
      builder: (context, _) {
        final color = Color.lerp(baseColor, highlightColor, pulse.value) ?? baseColor;
        return line(color);
      },
    );
  }
}
