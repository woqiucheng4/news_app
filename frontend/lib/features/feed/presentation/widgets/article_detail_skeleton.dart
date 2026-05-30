import 'package:flutter/material.dart';

import '../../../../shared/widgets/skeleton_line.dart';
import '../../../../shared/widgets/skeleton_pulse.dart';

class ArticleDetailSkeleton extends StatelessWidget {
  const ArticleDetailSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonPulse(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const SkeletonLine(width: 96, height: 28),
          const SizedBox(height: 16),
          SkeletonLine(width: MediaQuery.sizeOf(context).width - 32, height: 24),
          const SizedBox(height: 8),
          SkeletonLine(width: MediaQuery.sizeOf(context).width - 32, height: 24),
          const SizedBox(height: 8),
          const SkeletonLine(width: 180, height: 24),
          const SizedBox(height: 16),
          const SkeletonLine(width: 120, height: 12),
          const SizedBox(height: 24),
          SkeletonLine(width: MediaQuery.sizeOf(context).width - 32, height: 14),
          const SizedBox(height: 8),
          SkeletonLine(width: MediaQuery.sizeOf(context).width - 32, height: 14),
          const SizedBox(height: 8),
          SkeletonLine(width: MediaQuery.sizeOf(context).width - 32, height: 14),
          const SizedBox(height: 8),
          const SkeletonLine(width: 220, height: 14),
          const SizedBox(height: 24),
          SkeletonLine(width: MediaQuery.sizeOf(context).width - 32, height: 44),
        ],
      ),
    );
  }
}
