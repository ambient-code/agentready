---
layout: page
title: Strategic Roadmaps
---

Three paths to transform AgentReady from quality assessment tool to essential infrastructure for Red Hat's AI-assisted development initiative.

**Current Status**: v1.27.2 with LLM-powered learning, research commands, and batch assessment ([learn more](user-guide#bootstrap-your-repository))

**Target Audience**: Engineering leadership, product managers, and teams evaluating AgentReady adoption

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Roadmap 1: The Compliance Engine](#roadmap-1-the-compliance-engine)
- [Roadmap 2: The Agent Coach](#roadmap-2-the-agent-coach)
- [Roadmap 3: The Intelligence Layer](#roadmap-3-the-intelligence-layer)
- [Roadmap Comparison](#roadmap-comparison)
- [Recommended Approach](#recommended-approach)
- [Getting Started Today](#getting-started-today)

---

## Executive Summary

AgentReady can evolve along three strategic paths, each building on our core strength: **systematically making codebases more effective for AI-assisted development**.

### The Three Roadmaps

| Roadmap | Vision | Timeline | Strategic Impact |
|---------|--------|----------|------------------|
| **🏅 Compliance Engine** | Quality gate for AI tools | 6-8 weeks | Adoption velocity via enforcement |
| **🤖 Agent Coach** | AI-powered remediation | 8-10 weeks | Retention via assistance |
| **🧠 Intelligence Layer** | Codebase understanding platform | 10-12 weeks | Platform moat |

### Recommended Path

**Start with Roadmap 1, then evolve:**

- **Months 1-2**: Implement compliance features → fastest path to adoption
- **Months 3-4**: Layer in AI-powered fixes → convert enforcement to assistance
- **Months 5-6**: Build out API/platform → leverage data from mature deployment

This progression maximizes **adoption velocity** (enforcement), **retention** (AI assistance), and **strategic positioning** (platform moat).

---

## Roadmap 1: The Compliance Engine

**Agent-Ready Certification as Quality Gate**

### Vision

Make AgentReady a required quality gate for Red Hat's AI-assisted development. Repositories must hit **Silver (60+)** to use AI tools, **Gold (75+)** for production deployments.

**Strategic Value**: Immediate adoption through mandate, establishes AgentReady as standard across Red Hat engineering.

### Timeline

**6-8 weeks** from v1.0 to production-ready compliance system

### Core Features

#### 1. GitHub Actions Integration

- **PR status checks** with pass/fail based on score threshold
- **Automated PR comments** with assessment summary and trend analysis
- **Custom certification levels** per team/product (override default thresholds)
- **Workflow templates** for easy adoption

#### 2. Organization Dashboard

- **Leaderboard** showing all repositories with scores and certification levels
- **Trend tracking** over time (score improvements, regression detection)
- **Team rollups** aggregating scores by team/product
- **Executive reporting** with high-level metrics and health indicators

#### 3. Automated Remediation (`agentready align`)

- **Template-based fixes** for common issues (missing files, standard configs)
- **One-click remediation** from HTML reports
- **Batch operations** to fix multiple issues at once
- **Preview mode** showing what will change before applying

#### 4. Interactive Reports

- **"Fix This" buttons** in HTML reports triggering automated remediation
- **Issue creation** directly from report findings
- **Copy-paste commands** for manual remediation
- **Progress tracking** showing improvement over time

#### 5. Customizable Certification

- **Team-specific thresholds** (e.g., RHOAI requires Gold, others Silver)
- **Product-specific attributes** (enable/disable based on project type)
- **Custom scoring weights** via configuration files
- **Exemption workflows** for special cases with approval process

### Adoption Strategy

#### Phase 1: Dogfooding (Week 1-2)

- **Apply to AgentReady itself** and achieve Platinum certification
- **Document process** and create adoption playbook
- **Identify pain points** and refine UX

#### Phase 2: Friendly Pilot (Week 3-4)

- **Recruit 3 teams**: RHOAI, RHEL AI, OpenShift AI
- **Target**: Each team reaches Silver (60+) within 2 weeks
- **Collect feedback** on automation, report quality, remediation guidance
- **Iterate** based on real-world usage

#### Phase 3: Executive Mandate (Week 5-6)

- **Steven Huels backing**: Announce requirement for AI tool usage
- **Policy**: New AI-assisted projects must hit Silver before tool access
- **Enforcement**: GitHub App integration blocks AI tool PRs if score < threshold
- **Communication**: Engineering-wide announcement with training resources

#### Phase 4: Scale Deployment (Week 7-8)

- **GitHub App integration** for automatic repository onboarding
- **100+ repos** with AgentReady checks enabled
- **Self-service** adoption via bootstrap command
- **Success stories** showcasing teams that improved scores

### Success Metrics

#### Adoption Metrics

- **100+ repositories** with AgentReady checks in 8 weeks
- **80% of active repos** hit Silver (60+) in 12 weeks
- **20+ teams** actively using dashboard and reports

#### Impact Metrics

- **70% reduction** in "agent can't understand my repo" issues
- **50% faster** AI tool onboarding (better codebase context)
- **90% positive feedback** from pilot teams

#### Business Metrics

- **Reduced support burden** for AI tools (better-prepared codebases)
- **Improved AI tool effectiveness** (higher quality context)
- **Cultural shift** toward agent-ready practices

---

## Roadmap 2: The Agent Coach

**Real-Time Remediation & Learning**

### Vision

Transform AgentReady from static scanner to **interactive AI coach** that not only identifies issues but fixes them automatically with Claude-powered suggestions.

**Strategic Value**: Converts enforcement (Roadmap 1) into assistance, dramatically reducing friction and improving developer experience.

### Timeline

**8-10 weeks** from Roadmap 1 completion to AI-powered coach

### Core Features

#### 1. Claude-Powered Fix Generation

- **Type annotations**: Auto-add type hints to Python functions
- **Docstrings**: Generate Google-style docstrings from function signatures
- **Test generation**: Create pytest tests for uncovered functions
- **Refactoring**: Simplify complex functions flagged by assessors
- **Context-aware**: Uses repository context (CLAUDE.md, existing patterns)

#### 2. Fix Preview & Approval Workflow

- **Show diff** before applying changes
- **Interactive approval** (approve all, approve individually, reject)
- **Undo capability** to revert AI changes
- **Learn from feedback** (track which fixes get accepted/rejected)

#### 3. VS Code Extension (Optional)

- **Real-time assessment** as you code
- **Inline suggestions** for agent-readiness improvements
- **Quick fixes** via VS Code actions
- **Dashboard view** showing repository score and trends

#### 4. Claude Code Agent Integration

- **Agent-native interface** for remediation
- **Conversational fixes**: "Make this repository Gold-certified"
- **Contextual suggestions** based on project patterns
- **Automated PR creation** with fixes

#### 5. Automated PR Campaigns

- **Scheduled remediation**: Weekly PRs addressing low-hanging fruit
- **Batch improvements**: Fix similar issues across multiple files
- **Team review**: Auto-assign reviewers via CODEOWNERS
- **Continuous improvement**: Gradually increase score over time

#### 6. Telemetry & Learning

- **Track fix acceptance rate** (which AI fixes get merged)
- **Identify patterns** in successful vs rejected fixes
- **Improve suggestions** based on repository-specific preferences
- **Personalized coaching**: Adapt to team coding style

### Adoption Strategy

#### Phase 1: Build AI Fix Engine (Week 1-3)

- **Integrate Claude API** for fix generation
- **Implement core fixers**: Type annotations, docstrings, tests
- **Test on AgentReady codebase** (dogfooding)
- **Achieve >80%** AI fix acceptance rate internally

#### Phase 2: Pilot with RHOAI (Week 4-6)

- **Deploy to RHOAI team** as early adopters
- **Target**: 50+ AI-generated PRs merged
- **Collect feedback** on fix quality, UX, workflow integration
- **Iterate** based on real-world usage

#### Phase 3: VS Code Extension Launch (Week 7-8)

- **Publish to Red Hat extension registry**
- **Marketing**: Demo at engineering all-hands
- **Tutorial**: Step-by-step guide for installation and usage
- **Support**: Office hours for questions and feedback

#### Phase 4: Enable Auto-PR Campaigns (Week 9-10)

- **Opt-in system**: Teams enable automated weekly PRs
- **Guardrails**: Require approval, limit batch size
- **Metrics dashboard**: Track PRs created, merged, rejected
- **Success stories**: Highlight teams with highest improvement rates

### Success Metrics

#### AI Fix Quality

- **>75% of AI-generated fixes** merged without changes
- **<5% of AI fixes** cause regressions or test failures
- **90% developer satisfaction** with fix quality

#### Efficiency Gains

- **90% reduction** in time to fix agent-readiness (2 hours → 10 mins)
- **5+ PRs merged** per repository per quarter
- **50% reduction** in manual remediation effort

#### Adoption Metrics

- **500+ developers** using AI fix generation monthly
- **100+ repositories** with auto-PR campaigns enabled
- **1,000+ AI fixes** merged across Red Hat

---

## Roadmap 3: The Intelligence Layer

**Codebase Understanding Platform**

### Vision

Evolve AgentReady into a **foundational intelligence layer** for ALL Red Hat AI/agent tools. Become the source of truth for codebase context, structure, and agent-readiness.

**Strategic Value**: Platform moat—AgentReady data powers multiple AI products, creating lock-in and strategic positioning.

### Timeline

**10-12 weeks** from Roadmap 2 completion to platform launch

### Core Features

#### 1. REST API for Repository Insights

- **Assessment endpoint**: Get current score, findings, certification level
- **Structure endpoint**: Codebase layout, file organization, dependencies
- **Context endpoint**: Auto-generated summaries, key patterns, tech stack
- **Dependency endpoint**: Library versions, security vulnerabilities, freshness
- **Agent capability matching**: Which agents work best with this repo

#### 2. Auto-Generated Context Files

- **Dynamic CLAUDE.md**: Keep agent context files up-to-date automatically
- **Repomix integration**: Generate compressed context for token-limited tools
- **Custom templates**: Per-team context file formats
- **Version control**: Track context file changes over time

#### 3. Agent Capability Matching

- **Agent profiles**: Define capabilities of different AI agents/tools
- **Compatibility scoring**: How well does repo match agent requirements
- **Recommendations**: "This repo works best with Claude Code, not GitHub Copilot"
- **Gap analysis**: What's missing for optimal agent usage

#### 4. Cross-Repository Intelligence

- **Pattern detection**: Identify common practices across successful repos
- **Best practice propagation**: "Top-rated repos use X pattern, suggest for yours"
- **Anomaly detection**: Flag unusual patterns (security risks, anti-patterns)
- **Benchmarking**: Compare your repo to similar projects

#### 5. Integration with Red Hat AI Products

- **RHOAI integration**: Assess training data repositories for quality
- **RHEL AI integration**: Optimize model deployment repositories
- **Instructlab integration**: Improve knowledge base repository structure
- **CI/CD platform**: Gate deployments on agent-readiness scores

#### 6. Plugin Architecture

- **Custom assessors**: Teams can add product-specific checks
- **Community plugins**: Marketplace for third-party assessors
- **Language-specific packs**: Deep analysis for specific languages
- **Industry standards**: Compliance checks (HIPAA, SOC2, etc.)

#### 7. Historical Analysis & Predictive Insights

- **Trend prediction**: Forecast score trajectory based on commit patterns
- **Risk analysis**: Predict likelihood of agent failures based on recent changes
- **Churn correlation**: Identify teams with low scores and high support burden
- **ROI tracking**: Measure impact of agent-readiness on development velocity

### Adoption Strategy

#### Phase 1: Build API & Deploy (Week 1-4)

- **Design REST API** following OpenAPI spec
- **Implement core endpoints** (assessment, structure, context)
- **Deploy to Red Hat OpenShift** with HA setup
- **Documentation**: API reference, integration guides, SDKs

#### Phase 2: Partner with AI Initiatives (Week 5-7)

- **Recruit 2 partners**: RHOAI and CI/CD platform teams
- **Build integrations**: Connect their tools to AgentReady API
- **Demonstrate value**: Show how context data improves their products
- **Collect feedback**: Refine API based on real integration needs

#### Phase 3: Engineering Summit Demo (Week 8-9)

- **Keynote demo**: Show cross-product integration at Red Hat summit
- **Technical sessions**: Deep-dive workshops on API usage
- **Office hours**: Help teams integrate with their products
- **Success stories**: Case studies from pilot partners

#### Phase 4: Expand to External Partners (Week 10-12)

- **GitHub partnership**: Explore native integration with GitHub
- **JetBrains partnership**: Integrate with IntelliJ, PyCharm
- **Claude Code**: Become default codebase context provider
- **Open source**: Release core API as open source for community adoption

### Success Metrics

#### Platform Adoption

- **5+ Red Hat AI products** integrate with AgentReady API
- **3+ external partners** using AgentReady data
- **10,000+ API calls per day**

#### Data Quality

- **90% of auto-generated CLAUDE.md files** used without modification
- **95% uptime** for API service
- **<100ms latency** for assessment endpoint

#### Strategic Impact

- **AgentReady as standard**: Referenced in Red Hat AI strategy docs
- **Competitive advantage**: Unique codebase intelligence layer
- **Revenue opportunity**: Potential SaaS offering for external customers

---

## Roadmap Comparison

### Feature Matrix

| Feature | Compliance Engine | Agent Coach | Intelligence Layer |
|---------|-------------------|-------------|-------------------|
| **GitHub Actions Integration** | ✅ Core | ✅ Enhanced | ✅ API-powered |
| **Organization Dashboard** | ✅ Core | ✅ Enhanced | ✅ Enterprise |
| **Automated Remediation** | ✅ Templates | ✅ AI-powered | ✅ Cross-repo |
| **Interactive Reports** | ✅ Basic | ✅ AI suggestions | ✅ Predictive |
| **Custom Certification** | ✅ Core | ✅ Core | ✅ Pluggable |
| **AI Fix Generation** | ❌ | ✅ Core | ✅ Advanced |
| **VS Code Extension** | ❌ | ✅ Optional | ✅ Full IDE suite |
| **Claude Code Integration** | ❌ | ✅ Core | ✅ Native API |
| **Auto-PR Campaigns** | ❌ | ✅ Core | ✅ Cross-repo |
| **REST API** | ❌ | ❌ | ✅ Core |
| **Auto-generated Context** | ❌ | ❌ | ✅ Core |
| **Agent Capability Matching** | ❌ | ❌ | ✅ Core |
| **Cross-repo Intelligence** | ❌ | ❌ | ✅ Core |
| **Plugin Architecture** | ❌ | ❌ | ✅ Core |
| **Historical Analysis** | ❌ | ❌ | ✅ Core |

### Timeline & Dependencies

```
Roadmap 1: Compliance Engine (Weeks 1-8)
├── GitHub Actions integration (Week 1-2)
├── Organization dashboard (Week 3-4)
├── Automated remediation (Week 5-6)
└── Scale deployment (Week 7-8)

Roadmap 2: Agent Coach (Weeks 9-18) [requires Roadmap 1]
├── AI fix engine (Week 9-11)
├── RHOAI pilot (Week 12-14)
├── VS Code extension (Week 15-16)
└── Auto-PR campaigns (Week 17-18)

Roadmap 3: Intelligence Layer (Weeks 19-30) [requires Roadmap 2]
├── REST API build (Week 19-22)
├── Partner integrations (Week 23-25)
├── Summit demo (Week 26-27)
└── External partnerships (Week 28-30)
```

### Strategic Positioning

| Dimension | Compliance Engine | Agent Coach | Intelligence Layer |
|-----------|-------------------|-------------|-------------------|
| **Adoption Driver** | Enforcement (mandate) | Assistance (value) | Integration (ecosystem) |
| **Market Position** | Internal tool | Developer tool | Platform |
| **Revenue Model** | Cost center | Productivity gain | SaaS potential |
| **Competitive Moat** | Low (policy-based) | Medium (AI quality) | High (data network effects) |
| **Strategic Value** | Enabler | Differentiator | Foundation |

---

## Recommended Approach

### Why Sequential Execution?

**Start with Roadmap 1, then layer in 2 and 3:**

#### Months 1-2: Compliance Engine

- **Fastest path to adoption** via executive mandate
- **Establishes baseline** for all repositories
- **Generates data** for AI training and pattern detection
- **Proves value** with concrete metrics (adoption, score improvements)

#### Months 3-4: Agent Coach

- **Converts enforcement to assistance** (carrot after stick)
- **Improves developer experience** dramatically
- **Increases engagement** (from compliance to eager usage)
- **Builds trust** in AI-generated fixes

#### Months 5-6: Intelligence Layer

- **Leverages mature deployment** (100+ repos with rich data)
- **Enables cross-product synergies** (RHOAI, RHEL AI, etc.)
- **Creates platform moat** (hard to replicate data advantage)
- **Opens revenue opportunities** (external partnerships, SaaS)

### Why NOT Parallel Development?

**Parallel development risks:**

- **Resource constraints**: Stretching team too thin reduces quality
- **Integration complexity**: Features designed independently may not mesh well
- **Data dependency**: Roadmap 3 needs data from Roadmap 1 deployment
- **Market feedback**: Each phase informs next (pilot learnings, usage patterns)

### Success Checkpoints

**Proceed to next roadmap only if:**

| Checkpoint | Criteria |
|------------|----------|
| **Roadmap 1 → 2** | 50+ repos at Silver, 80% pilot satisfaction, <5% regression rate |
| **Roadmap 2 → 3** | 75% AI fix acceptance, 200+ repos using coach, 10+ teams with auto-PRs |
| **Roadmap 3 → External** | 5+ internal integrations, 10K+ API calls/day, 95% uptime |

---

## Getting Started Today

### For Individual Developers

```bash
# Bootstrap your repository now
cd /path/to/your/repo
agentready bootstrap .

# Review generated files
git status

# Commit and see automated assessment on next PR
git add . && git commit -m "build: Bootstrap agent-ready infrastructure"
git push
```

**Learn more**: [Bootstrap tutorial →](user-guide.md#bootstrap-your-repository)

### For Team Leads

1. **Assess current state**: Run `agentready assess .` on your team's repos
2. **Set team target**: Decide on certification level (Silver, Gold, Platinum)
3. **Bootstrap infrastructure**: Enable GitHub Actions via bootstrap command
4. **Track progress**: Use reports to monitor score improvements
5. **Share results**: Include assessment scores in team metrics

**Learn more**: [User guide →](user-guide.md)

### For Engineering Leadership

1. **Pilot program**: Recruit 3 friendly teams for initial rollout
2. **Success metrics**: Define KPIs (adoption rate, score targets, velocity impact)
3. **Executive sponsorship**: Align with AI-assisted development strategy
4. **Policy development**: Draft agent-readiness requirements for AI tool access
5. **Communication plan**: Announce mandate with clear timelines and support

**Contact**: Reach out to [Jeremy Eder](mailto:jeder@redhat.com) to discuss strategic rollout

---

## Next Steps

- **[User Guide](user-guide.md)** — Install and run your first assessment
- **[Developer Guide](developer-guide.md)** — Contribute to AgentReady development
- **[Attributes Reference](attributes.md)** — Understand the 25 agent-ready attributes
- **[API Reference](api-reference.md)** — Integrate AgentReady into your tools
- **[Examples](examples.md)** — See real-world assessment reports

---

**Questions?** Join the discussion on [GitHub](https://github.com/ambient-code/agentready/issues) or contact the AgentReady team.

**Last Updated**: 2025-11-21
