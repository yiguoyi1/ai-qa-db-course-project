# AI QA Product Promos

Generated product promo assets for the AI QA community website.

## Files

- `ai-qa-community-enterprise-saas-promo.mp4` - primary H.264 video, 1920x1080, 60 fps, 28 seconds, rendered at 1.5x speed from the 42-second source timeline.
- `ai-qa-community-enterprise-saas-promo-poster.png` - poster frame, 1920x1080.
- `ai-qa-community-logo-aiq.png` - standalone AI + Q lettermark preview, 1024x1024 transparent PNG.
- `generate_enterprise_saas_promo.swift` - deterministic AVFoundation generator for the enterprise SaaS promo.

## Enterprise Storyboard

1. 0-3.3s: Brand reveal and positioning.
2. 3.3-7.3s: Fragmented information and answer discovery tension.
3. 7.3-12s: Information convergence into a central product structure.
4. 12-18s: Three product value cards: intelligent search, management, collaboration.
5. 18-23.3s: Abstract workspace for knowledge management, queries, collaboration, and analytics.
6. 23.3-28s: Brand return and CTA.

## Regenerate

```bash
swift promo/generate_enterprise_saas_promo.swift
swift promo/generate_enterprise_saas_promo.swift --logo /Users/corld/Desktop/软件系统开发/Facebook/promo/ai-qa-community-logo-aiq.png
```
