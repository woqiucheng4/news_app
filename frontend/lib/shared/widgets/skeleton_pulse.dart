import 'package:flutter/material.dart';

import 'ticker_mode_animation.dart';

class SkeletonPulse extends StatefulWidget {
  const SkeletonPulse({
    super.key,
    required this.child,
  });

  final Widget child;

  static Animation<double>? animationOf(BuildContext context) {
    return context
        .dependOnInheritedWidgetOfExactType<_SkeletonPulseScope>()
        ?.animation;
  }

  @override
  State<SkeletonPulse> createState() => _SkeletonPulseState();
}

class _SkeletonPulseState extends State<SkeletonPulse>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _animation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    syncAnimationWithTickerMode(context, _controller, reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _SkeletonPulseScope(
      animation: _animation,
      child: widget.child,
    );
  }
}

class _SkeletonPulseScope extends InheritedWidget {
  const _SkeletonPulseScope({
    required this.animation,
    required super.child,
  });

  final Animation<double> animation;

  @override
  bool updateShouldNotify(_SkeletonPulseScope oldWidget) {
    return animation != oldWidget.animation;
  }
}
