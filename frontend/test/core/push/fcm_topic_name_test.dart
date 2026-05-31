import 'package:flutter_test/flutter_test.dart';
import 'package:newsflow_frontend/core/push/fcm_topic_name.dart';

void main() {
  test('buildFcmTopicName prefixes topic id', () {
    const topicId = '550e8400-e29b-41d4-a716-446655440000';
    expect(buildFcmTopicName(topicId), 'topic_$topicId');
  });
}
