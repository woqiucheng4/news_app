# Feature Landscape: NewsFlow

**Domain:** AI-powered information aggregation and news reader
**Researched:** 2026-05-08
**Overall confidence:** MEDIUM

## Methodology

Analyzed 9 products across the information aggregation ecosystem:

| Product | Type | Key Insight |
|---------|------|-------------|
| Google News | Algorithmic aggregator | Personalization + publisher ecosystem dominance |
| Apple News | Curated + algorithmic | Editorial curation + Apple Intelligence AI summaries |
| Feedly | RSS reader + AI | Leo AI for prioritization, deduplication, topic tracking |
| Inoreader | Power-user RSS | Automation rules, AI summarization, full content extraction, TTS |
| Flipboard | Social magazine reader | Magazine-style curation, user-created collections, Fediverse |
| SmartNews | Mobile-first reader | Multi-perspective coverage, local news, fast reading UX |
| Artifact (RIP) | AI-native social reader | TikTok-style feed, clickbait rewriting, social profiles |
| Toutiao | AI recommendation engine | Pure algorithmic personalization, multi-format content |
| Jike | Interest social network | Community circles, social feed, podcast integration |

---

## Table Stakes

Missing any of these = users leave. Every competitor has them.

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| **Content aggregation** | Core value proposition -- must pull content from multiple sources | Medium | RSS + scraper, already in PROJECT.md |
| **Topic/interest subscription** | Users must declare what they care about | Low | Categories, keywords, custom feeds |
| **Personalized feed** | Users expect the system to learn what they like | Medium | Basic collaborative filtering or engagement-based ranking |
| **Cross-platform (Web + Mobile)** | Users consume news on multiple devices | High | Flutter covers this; must sync state |
| **Push notifications** | Breaking news is time-sensitive | Low | FCM, already in PROJECT.md |
| **User accounts** | Personalization requires identity | Low | Email + Google/Apple OAuth, already in PROJECT.md |
| **Article save/bookmark** | "Read later" is universal expectation | Low | Simple CRUD |
| **Search** | Find specific topics in aggregated content | Medium | Full-text search on PostgreSQL |
| **Share to external apps** | Users share news via messaging/social | Low | Native share sheet integration |
| **Source attribution + link-out** | Legal and ethical requirement; users want to verify | Low | Always show source name, link to original |
| **Offline reading of saved items** | Users read during commute, flights | Medium | Cache summaries locally, not full articles |

**Confidence:** HIGH -- These are universally present across all 9 analyzed products.

---

## Differentiators

Features that create competitive advantage. Not all competitors have these.

### Tier 1: Core Differentiators (align with PROJECT.md vision)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI-generated summaries** | The primary value prop of NewsFlow; users get the gist without reading full articles | Medium | Claude Haiku / GPT-4o-mini for per-article summaries; already specified |
| **Comprehensive daily briefing** | "Your morning news in 5 minutes"; one curated digest per day | Medium | Aggregate top N stories across all subscriptions into a single summary |
| **Multi-source synthesis** | When multiple sources cover the same event, produce ONE merged summary instead of N separate cards | High | Requires event clustering + merge summarization; powerful but complex |
| **Smart notification filtering** | Only push truly important updates, not every article | Medium | AI scores importance; prevents notification fatigue |

### Tier 2: Engagement Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Multi-perspective coverage** | Show how different sources cover the same event (SmartNews-style slider) | High | Requires event clustering + political/source diversity scoring |
| **AI topic monitoring (natural language)** | "Tell me when something interesting happens about X" -- users describe topics in plain English | Medium | NLP-based matching vs rigid keyword rules |
| **Audio narration (TTS)** | Listen to summaries while commuting; accessibility | Medium | Cloud TTS API; Inoreader and Apple News both offer this |
| **Clickbait detection/rewriting** | Clean up sensational headlines; Artifact's killer feature | Low-Medium | LLM-based headline quality scoring + rewriting |
| **Full content extraction** | Read the article within the app without popup/cookie walls | Medium | Readability-style extraction; Inoreader offers this |
| **Automation rules** | Power users create "if X then Y" rules for content flow | Medium | Inoreader's strongest feature; may be overkill for MVP |

### Tier 3: Retention Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Reading statistics** | Show users their reading habits; gamification element | Low | Articles read, topics explored, time saved via summaries |
| **Weekly/monthly digest email** | Re-engage dormant users with curated recap | Low | Scheduled email with top stories |
| **Source quality scoring** | Show trustworthiness indicators per source | Medium | Fact-check database + source reputation metrics |
| **Custom AI analysis (premium)** | Deep dive on specific topics; paid-tier feature | Medium | Use larger models for paid users; in PROJECT.md |

**Confidence:** MEDIUM -- Tier 1 aligns well with PROJECT.md. Tier 2/3 based on competitive analysis; actual user demand unvalidated.

---

## Anti-Features

Features to explicitly NOT build. These either create legal risk, scope creep, or misalign with the product vision.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Full article caching** | Copyright risk, storage costs, legal liability | Show summaries + link to original; already in PROJECT.md |
| **Comment/discussion system** | Massive moderation burden; toxic community management; not core to information aggregation | Link to source site's own comments if needed; defer to v2+ |
| **User-generated content / news creation** | Content moderation nightmare; regulatory risk; misaligned with "aggregator" identity | Focus on curating existing content, not creating new content |
| **Social network features** | Artifact's mistake -- tried to become a social app; dilutes focus | Keep social to "share externally" only; no profiles, followers, feeds |
| **Video content aggregation** | Different content type with different UX, infrastructure, and cost | Stay focused on text/summary format; video is a different product |
| **In-app browser / reader mode** | Copyright gray area; maintenance burden for rendering diverse sites | Link out to original; the summary IS the value |
| **Clickbait optimization / engagement metrics** | Incentivizes sensationalism; contradicts "efficient information" positioning | Optimize for "information density" not "time spent" |
| **Ad-supported free tier** | Aligns with PROJECT.md decision; ads conflict with clean UX | Freemium + subscription; already decided |
| **Echo chamber reinforcement** | Over-personalization creates information bubbles; ethical concern | Inject diversity signals; offer "explore opposite views" option |
| **Payment / e-commerce** | Scope creep; completely different domain | Out of scope |
| **AI chat / conversation (v1)** | Significantly increases complexity and cost; PROJECT.md explicitly defers | Simple summaries in v1; conversational AI in v2 |
| **Newsletter creation / forwarding** | Different product; Inoreader offers it but it's niche | Not core to "information consumption" positioning |

**Confidence:** HIGH -- Based on PROJECT.md decisions and competitive failure analysis (Artifact shut down partly due to scope creep into social).

---

## Feature Dependencies

```
User accounts
  --> Personalized feed
  --> Topic/interest subscription
  --> Push notifications
  --> Saved articles/bookmarks
  --> Reading statistics
  --> Free/paid tier differentiation

Content aggregation (RSS + scraper)
  --> Article storage
  --> AI summaries (needs raw content)
  --> Full-text search
  --> Source attribution

AI summaries
  --> Daily briefing (aggregates summaries)
  --> Multi-source synthesis (merges summaries)
  --> Audio narration (TTS on summaries)
  --> Clickbait detection (LLM-based)
  --> Custom AI analysis (premium)

Event clustering (future)
  --> Multi-source synthesis
  --> Multi-perspective coverage

Personalized feed
  --> Smart notification filtering (needs importance scoring)
  --> AI topic monitoring (needs NLP matching)
```

---

## MVP Recommendation

### Must Ship (v1)

Prioritize in this order:

1. **Content aggregation** -- RSS + basic scraper; the foundation of everything
2. **Topic/interest subscription** -- Users declare interests via categories + keywords
3. **User accounts** -- Email + Google/Apple OAuth
4. **AI-generated summaries** -- The core value prop; per-article summarization
5. **Personalized feed** -- Basic engagement-based ranking
6. **Cross-platform** -- Flutter mobile app + web
7. **Push notifications** -- Breaking news + daily briefing
8. **Article save/bookmark** -- Read later functionality
9. **Search** -- Full-text across aggregated content
10. **Source attribution + link-out** -- Legal necessity

### Should Ship (v1.1)

- **Daily briefing** -- One digest per day; high retention value, moderate effort
- **Smart notification filtering** -- Prevent fatigue; critical for retention
- **Share to external** -- Viral growth mechanism
- **Offline reading** -- Commuter use case

### Defer to v2

- **Multi-source synthesis** -- Powerful but high complexity; needs event clustering
- **Multi-perspective coverage** -- Requires source diversity scoring
- **Audio narration (TTS)** -- Nice to have, not essential
- **Clickbait detection** -- Interesting but not a dealbreaker
- **Full content extraction** -- Copyright gray area; defer
- **Automation rules** -- Power user feature; too complex for MVP
- **AI topic monitoring** -- Natural language topic matching; v2 feature

### Never Build

- Full article caching, comments, social network, video, UGC, ads, in-app browser

---

## Competitive Positioning

| Dimension | Google News | Apple News | Feedly | Inoreader | NewsFlow (target) |
|-----------|-------------|------------|--------|-----------|-------------------|
| AI summaries | Emerging (Gemini) | Apple Intelligence | Leo (basic) | Intelligence | **Core value prop** |
| Source breadth | Very high | Medium (curated) | User-driven | User-driven | **RSS + scraper hybrid** |
| Personalization | Strong | Medium | Medium | Low (manual) | **Topic + AI hybrid** |
| UX complexity | Low | Low | Medium | High | **Low (Notion-like)** |
| Price | Free | Free + $10/mo | Free + $6/mo | Free + $5/mo | **Freemium** |
| Target audience | Mass market | Apple ecosystem | Tech/professionals | Power users | **Global info consumers** |
| Social features | None | None | None | None | **None (by design)** |

**NewsFlow's niche:** AI-first summaries with clean UX, positioned between Google News (too algorithmic, no summaries) and Inoreader (too complex, no AI summaries as core feature).

---

## Sources

| Source | URL | Confidence |
|--------|-----|------------|
| Inoreader Features | https://www.inoreader.com/features/ | HIGH |
| Inoreader Consume Features | https://www.inoreader.com/features/consume | HIGH |
| SmartNews | https://www.smartnews.com/en/ | HIGH |
| Google News Help Center | https://support.google.com/news/answer/6262620 | MEDIUM |
| Artifact Wikipedia | https://en.wikipedia.org/wiki/Artifact_(app) | HIGH |
| Apple News+ Wikipedia | https://en.wikipedia.org/wiki/Apple_News%2B | HIGH |
| Flipboard Wikipedia | https://en.wikipedia.org/wiki/Flipboard | HIGH |
| Toutiao Wikipedia | https://zh.wikipedia.org/wiki/%E4%BB%8A%E6%97%A5%E5%A4%B4%E6%9D%A1 | HIGH |
| Jike Wikipedia | https://zh.wikipedia.org/wiki/%E5%8D%B3%E5%88%BB | MEDIUM |

---

*Researched: 2026-05-08. Confidence: MEDIUM overall (product features well-documented, but user demand for specific features is unvalidated for this project).*
