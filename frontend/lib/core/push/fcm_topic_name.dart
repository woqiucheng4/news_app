/// Build a stable FCM topic name from a backend topic UUID.
String buildFcmTopicName(String topicId) => 'topic_${topicId.trim()}';
