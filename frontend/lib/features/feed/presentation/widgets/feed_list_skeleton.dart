import 'package:flutter/material.dart';

import '../../../../shared/widgets/skeleton_line.dart';
import '../../../../shared/widgets/skeleton_pulse.dart';

class FeedListSkeleton extends StatelessWidget {
  const FeedListSkeleton({super.key, this.itemCount = 4});

  final int itemCount;

  @override
  Widget build(BuildContext context) {
    final contentWidth = MediaQuery.sizeOf(context).width - 64;

    return SkeletonPulse(
      child: ListView.builder(
        padding: const EdgeInsets.only(top: 8, bottom: 24),
        physics: const NeverScrollableScrollPhysics(),
        itemCount: itemCount,
        itemBuilder: (context, index) {
          return Card(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SkeletonLine(width: 72, height: 24),
                  const SizedBox(height: 12),
                  SkeletonLine(width: contentWidth, height: 18),
                  const SizedBox(height: 8),
                  const SkeletonLine(width: 180, height: 12),
                  const SizedBox(height: 12),
                  SkeletonLine(width: contentWidth, height: 14),
                  const SizedBox(height: 6),
                  SkeletonLine(width: contentWidth, height: 14),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
