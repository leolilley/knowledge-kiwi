# Integrated Kiwi-SDK Architecture: "Orchestrated Reasoning"

## Executive Summary

This document proposes a **merged architecture** that combines:
- **Kiwi's strengths**: Multi-agent orchestration, global registry, knowledge aggregation
- **Claude Agent SDK's strengths**: Reasoning loop mechanics, pragmatic tool selection, Unix composability

**Result**: An agent system where:
- Coordinator (Kiwi) manages agent hierarchy and resource coordination
- Individual agents (SDK) reason through gather → think → act → verify cycle
- Agents autonomously select execution mode (tool vs bash vs code)
- Global registry captures both orchestration patterns and agent reasoning learnings
- Knowledge flows bidirectionally: orchestration improves agents, agent learnings improve orchestration

---

## 1. Core Architecture

### Current Kiwi Model (Agent-Centric)

```
Master Coordinator
├─ spawns Sub-agents (executes directives)
├─ manages shared resources
└─ enforces constraints

Sub-agent behavior: "execute directive"
```

### Proposed Integrated Model (Reasoning-Orchestrated)

```
Layer 1: Coordinator (Orchestration - Kiwi)
├─ Manages agent lifecycle
├─ Enforces resource constraints
├─ Routes work to specialized agents
└─ Aggregates learnings to Knowledge Kiwi

Layer 2: Sub-Agents (Reasoning Loop - SDK)
├─ Gather relevant context
├─ Reason about options
├─ Autonomously select execution: tool | bash | code_gen
├─ Verify results and recover from errors
└─ Report learnings to Knowledge Kiwi

Layer 3: Knowledge Graph (Learning - Kiwi)
├─ Stores agent reasoning patterns
├─ Stores orchestration patterns
├─ Enables pattern discovery across domains
└─ Tracks what works and what doesn't
```

### Execution Flow

```
User Request → Master Agent
               ↓
            Gather Context (SDK pattern)
            Think about approach (SDK pattern)
            Decide: Which sub-agents needed? (Coordinator logic)
            ↓
         Spawn Sub-Agent A
         ├─ Gather Context (local)
         ├─ Think about task
         ├─ Decide: tool? bash? code? (SDK decision)
         ├─ Execute
         ├─ Verify result
         └─ Report to Master + Knowledge Kiwi
         ↓
         Spawn Sub-Agent B (parallel or sequential)
         [same as above]
         ↓
         Coordinator aggregates results
         Updates Knowledge Kiwi
         Returns result to user
```

---

## 2. Enhanced Directive Format

### Current Kiwi Format
```xml
<directive name="instagram_campaign_orchestrator">
  <agent_architecture>
    <sub_agents>
      <agent name="dm_sender" count="3">
        <directive>send_instagram_dm.md</directive>
      </agent>
    </sub_agents>
  </agent_architecture>
  <coordination_logic>...</coordination_logic>
</directive>
```

### Proposed Integrated Format

```xml
<directive name="instagram_campaign_orchestrator" version="4.0.0">
  <metadata>
    <description>Instagram campaign with parallel agents and adaptive reasoning</description>
    <orchestration_pattern>hierarchical</orchestration_pattern>
    <sdk_integration>true</sdk_integration>
  </metadata>

  <!-- COORDINATOR AGENT (Kiwi) -->
  <coordinator_agent>
    <role>Campaign manager with adaptive resource allocation</role>
    <responsibilities>
      - Spawn and manage sub-agents
      - Monitor resource usage (rate limits, costs, context)
      - Handle failures and recovery
      - Aggregate learnings
      - Report to Knowledge Kiwi
    </responsibilities>
    
    <reasoning_loop>
      <gather>
        - User campaign parameters
        - Current resource state
        - Recent learnings from Knowledge Kiwi
        - Historical success patterns
      </gather>
      <think>
        - Optimal agent count for throughput
        - Which execution patterns worked last time
        - What rate limits to apply
        - Context rotation strategy
      </think>
      <act>
        - Spawn configured sub-agents
        - Distribute work
        - Monitor execution
        - Enforce constraints
      </act>
      <verify>
        - Check success metrics
        - Detect anomalies
        - Trigger recovery if needed
        - Update metrics for next run
      </verify>
    </reasoning_loop>
  </coordinator_agent>

  <!-- SUB-AGENTS (SDK) -->
  <sub_agents>
    <agent_group name="profile_researcher">
      <count>1</count>
      <directive>instagram_profile_analysis_sdk.md</directive>
      <role>Research target profiles</role>
      
      <!-- SDK Reasoning Loop for this Agent -->
      <reasoning_loop>
        <gather>
          <context>Search query from coordinator</context>
          <context>Known rate limits from Knowledge Kiwi</context>
          <context>Previous successful search patterns</context>
          <capability>API access, data processing tools</capability>
        </gather>
        
        <think>
          <decision>
            Should I use:
            (a) Instagram API tool (most direct)
            (b) Web scraping via bash + curl (less reliable)
            (c) Code generation for complex filtering logic
          </decision>
          <!-- Decision tree encoded -->
          <logic>
            if search_complexity > 3:
              use code_gen (complex filter logic)
            elif api_available:
              use tool (Instagram API)
            else:
              use bash (curl + jq parsing)
          </logic>
        </think>
        
        <act>
          <execution_mode>tool</execution_mode>
          <tool>instagram_api</tool>
          <query>{{search_params}}</query>
          <error_handling>
            on rate_limit:
              backoff = exponential(attempt)
              retry after backoff
              report to Knowledge Kiwi
          </error_handling>
        </act>
        
        <verify>
          <check>Did query succeed?</check>
          <check>Does result meet quality threshold?</check>
          <check>Any rate limiting warnings?</check>
          <recovery>
            if low_quality:
              refine parameters and retry
            if rate_limited:
              slow down, wait, report to Master
          </recovery>
          <learning>
            log execution time
            log success rate
            log what search parameters worked best
          </learning>
        </verify>
      </reasoning_loop>
    </agent_group>

    <agent_group name="dm_sender">
      <count>3</count>
      <directive>send_instagram_dm_sdk.md</directive>
      <role>Send DMs with autonomous rate management</role>
      
      <reasoning_loop>
        <gather>
          <context>Queue of profiles to message</context>
          <context>My agent_id and allocation</context>
          <context>Shared rate limit state (from Master)</context>
          <context>Knowledge Kiwi learnings: "what messages work?"</context>
          <capability>API tool, message templates, data validation</capability>
        </gather>
        
        <think>
          <decision>
            How should I send this message?
            (a) Use Instagram API tool (standard)
            (b) Use browser automation bash script
            (c) Generate custom message with code
          </decision>
          <logic>
            if message_is_template:
              use tool (faster, standard)
            elif message_needs_personalization:
              use code_gen (customize per profile)
            else:
              use bash (fallback)
          </logic>
          <strategy>
            Check rate limit budget:
            if budget_available:
              send now
            else:
              wait (Master will resume when limit resets)
          </strategy>
        </think>
        
        <act>
          <execution_mode>tool</execution_mode>
          <tool>instagram_dm_api</tool>
          <message>{{personalized_message}}</message>
          <rate_limit_check>
            - Ask Master: "Do I have budget?"
            - Wait if needed (Master coordinates all 3 agents)
            - Decrement shared budget after send
          </rate_limit_check>
        </act>
        
        <verify>
          <check>Message delivered successfully?</check>
          <check>Any errors or warnings?</check>
          <check>Rate limit warnings?</check>
          <recovery>
            if delivery_failed:
              retry up to 3 times with backoff
              report failure to Master
            if rate_limited:
              pause execution
              notify Master
              resume when Master signals
          </recovery>
          <learning>
            log message content → engagement
            log personalization level → response rate
            log timing → best send times
          </learning>
        </verify>
      </reasoning_loop>

      <!-- Coordinator enforces this constraint -->
      <coordination>
        <shared_rate_limit>
          <pool_size>90 DMs/day</pool_size>
          <per_agent_soft_limit>30 DMs/day</per_agent_soft_limit>
          <management>
            Master tracks budget
            Agents request permission before sending
            Master enforces global ceiling
          </management>
        </shared_rate_limit>
      </coordination>
    </agent_group>

    <agent_group name="response_monitor">
      <count>1</count>
      <directive>monitor_instagram_responses_sdk.md</directive>
      <role>Track engagement, update strategy</role>
      
      <reasoning_loop>
        <gather>
          <context>Recent sent messages and their IDs</context>
          <context>User engagement data</context>
          <context>Current Knowledge Kiwi learnings</context>
          <capability>Instagram API, analytics tools</capability>
        </gather>
        
        <think>
          <analysis>
            Analyze response patterns:
            - Which messages got replies? (high engagement)
            - Which were ignored? (low engagement)
            - Any patterns in timing? (sent at 9am → high response)
          </analysis>
          <decision>
            How should I gather this data?
            (a) Use analytics API tool (best)
            (b) Fetch raw data + bash processing
            (c) Code generation for complex analysis
          </decision>
          <logic>
            if simple_aggregation:
              use bash (curl + jq)
            else:
              use code_gen (pattern analysis)
          </logic>
        </think>
        
        <act>
          <execution_mode>code_gen</execution_mode>
          <analysis>
            Identify top-performing message templates
            Find optimal sending times
            Detect any account risks
          </analysis>
        </act>
        
        <verify>
          <check>Analysis complete and valid?</check>
          <check>Insights actionable?</check>
          <recovery>
            if analysis_failed:
              retry with different approach
              use fallback: simpler aggregation
          </recovery>
          <learning>
            Report to Knowledge Kiwi:
            - "Message type X gets Y% engagement"
            - "Optimal send time is Z"
            - "Watch out for account risk W"
          </learning>
        </verify>
      </reasoning_loop>

      <!-- Feedback loop to other agents -->
      <feedback_to_agents>
        <target>dm_sender agents</target>
        <message>Use message type X (highest engagement)</message>
        <frequency>Every 100 messages</frequency>
      </feedback_to_agents>
    </agent_group>
  </sub_agents>

  <!-- ORCHESTRATION (Kiwi) -->
  <coordination_logic>
    <sequence>
      1. Master gathers context (campaign params, state)
      2. Master thinks about approach (checks learnings, decides on agent mix)
      3. Master spawns profile_researcher (1)
      4. Waits for researcher to complete with qualified profiles
      5. Master thinks about optimal DM schedule (from Knowledge Kiwi insights)
      6. Master spawns dm_sender agents (3) in parallel
      7. Master spawns response_monitor (1) to run continuously
      8. Master monitors all agents:
         - Tracks rate limit budget (shared pool)
         - Pauses if limit near
         - Collects learnings
         - Handles failures
      9. Agents report to Master regularly (every 5 min status)
      10. Master aggregates results and learnings
    </sequence>

    <resource_management>
      <rate_limits>
        <pool>90 DMs/day shared across all agents</pool>
        <tracking>Master maintains central counter</tracking>
        <enforcement>
          Agents request permission before action
          Master grants/delays based on budget
          All agents respect Master's decision
        </enforcement>
        <learning>
          Knowledge Kiwi tracks if limit is still valid
          If Instagram changed limits, directive updates
        </learning>
      </rate_limits>

      <context_rotation>
        <trigger>When agent reaches 80% context</trigger>
        <procedure>
          1. Agent serializes state to JSON
          2. Master spawns fresh agent
          3. Fresh agent reads state, continues
          4. Old agent documents learnings, terminates
        </procedure>
        <learning>
          How long each agent type needs before rotation
          What state transfer mechanisms work best
        </learning>
      </context_rotation>

      <cost_optimization>
        <profile_researcher>
          <model>claude-opus</model>
          <reason>Once per campaign, complex analysis</reason>
          <cost>high, runs 1x</cost>
        </profile_researcher>
        <dm_sender>
          <model>claude-haiku</model>
          <reason>Simple message sending, runs many times</reason>
          <cost>low, runs 90x/day</cost>
        </dm_sender>
        <response_monitor>
          <model>claude-sonnet</model>
          <reason>Pattern analysis, moderate complexity</reason>
          <cost>medium, runs periodically</cost>
        </response_monitor>
      </cost_optimization>
    </resource_management>

    <failure_handling>
      <agent_failure>
        <detection>Agent misses check-in for 5 min</detection>
        <response>Master spawns replacement agent</response>
        <learning>Log what failed, update Knowledge Kiwi</learning>
      </agent_failure>
      <rate_limit_hit>
        <detection>Master detects budget exhausted</detection>
        <response>Pause all DM senders, notify all agents</response>
        <recovery>Resume when limit resets (next day)</recovery>
        <learning>Verify rate limit assumption with Knowledge Kiwi</learning>
      </rate_limit_hit>
      <account_block>
        <detection>DM agent gets "action block" error</detection>
        <response>Master terminates all agents immediately</response>
        <analysis>Master analyzes what led to block</analysis>
        <learning>
          Update Knowledge Kiwi with risk pattern
          Annealing: Update directive to prevent recurrence
          Example: "Reduce from 3 agents to 1 agent"
        </learning>
      </account_block>
    </failure_handling>

    <adaptation>
      <trigger>If success rate drops below threshold</trigger>
      <procedure>
        1. Master identifies which agent is underperforming
        2. Master queries Knowledge Kiwi for alternatives
        3. Master hot-swaps improved directive
        4. System continues without restart
      </procedure>
      <learning>
        Track which adaptations worked
        Share success with registry
      </learning>
    </adaptation>
  </coordination_logic>

  <!-- KNOWLEDGE INTEGRATION (Kiwi) -->
  <knowledge_integration>
    <agents_report_to>Knowledge Kiwi</agents_report_to>
    <learnings_captured>
      <agent>profile_researcher</agent>
      <learning>
        - Best search query formulations
        - Instagram API response patterns
        - Rate limit behavior
        - Profile qualification criteria that predict engagement
      </learning>
    </learnings_captured>
    <learnings_captured>
      <agent>dm_sender</agent>
      <learning>
        - Message templates ranked by engagement
        - Optimal send times
        - Account risk indicators
        - Personalization techniques that work
      </learning>
    </learnings_captured>
    <learnings_captured>
      <agent>response_monitor</agent>
      <learning>
        - Engagement pattern analysis
        - Correlation between message attributes and response
        - Temporal patterns (when users are most responsive)
      </learning>
    </learnings_captured>
    <learnings_captured>
      <agent>coordinator</agent>
      <learning>
        - Optimal agent count (1 vs 3 senders)
        - Rate limit budget accuracy
        - Context rotation timing
        - Cost per successful DM
      </learning>
    </learnings_captured>

    <feedback_loop>
      <from>Knowledge Kiwi</from>
      <to>Master Agent</to>
      <content>
        - Recent learnings about what works
        - Warnings about what failed
        - Updated rate limits
        - Suggested parameter adjustments
      </content>
      <timing>Before agent spawning, during execution</timing>
    </feedback_loop>
  </knowledge_integration>

  <!-- VERSION EVOLUTION (Kiwi Registry) -->
  <version_history>
    v1.0.0 (original)
    v2.0.0 (added coordination logic)
    v3.0.0 (context rotation, circuit breakers)
    v3.1.0 (cost optimization)
    v4.0.0 (integrated SDK reasoning loops)
      - Added explicit gather/think/act/verify to each agent
      - Added tool vs bash vs code decision logic
      - Enhanced error recovery
      - Improved Knowledge Kiwi integration
  </version_history>
</directive>
```

---

## 3. Three Updated Kiwi Tools

### 1. Context Kiwi: Enhanced Directive Format

**What's New:**
- Directives now include `<reasoning_loop>` for each agent
- Decision logic explicit and **machine-readable** (structured decision trees)
- Tool/bash/code selection encoded with **cost/success tradeoffs**
- Verification with **quantifiable success criteria**
- Knowledge queries with **standardized syntax**

**Structured Decision Trees:**

Instead of prose `<think>` blocks, use executable decision trees:

```xml
<think>
  <decision_tree name="execution_mode_selection">
    <node id="check_complexity">
      <condition>task.complexity</condition>
      <branches>
        <branch value="simple" goto="use_tool"/>
        <branch value="medium" goto="check_reliability"/>
        <branch value="complex" goto="use_code_gen"/>
      </branches>
    </node>
    
    <node id="check_reliability">
      <condition>tool.availability AND tool.success_rate > 0.9</condition>
      <branches>
        <branch value="true" goto="use_tool"/>
        <branch value="false" goto="use_bash"/>
      </branches>
    </node>
    
    <leaf id="use_tool">
      <action>tool</action>
      <tool_name>instagram_api</tool_name>
      <cost_estimate>0.001</cost_estimate>
      <success_rate>0.95</success_rate>
      <speed>fast</speed>
    </leaf>
    
    <leaf id="use_bash">
      <action>bash</action>
      <script>get_instagram_data.sh</script>
      <cost_estimate>0.0</cost_estimate>
      <success_rate>0.75</success_rate>
      <speed>medium</speed>
    </leaf>
    
    <leaf id="use_code_gen">
      <action>code_gen</action>
      <prompt>Generate custom filter logic for Instagram profiles matching criteria</prompt>
      <cost_estimate>0.05</cost_estimate>
      <success_rate>0.92</success_rate>
      <speed>slow</speed>
    </leaf>
  </decision_tree>
</think>
```

**Knowledge Query Syntax:**

Agents query Knowledge Kiwi with structured requests:

```xml
<gather>
  <knowledge_query>
    <source>knowledge_kiwi</source>
    <query_type>best_practices</query_type>
    <domain>instagram_messaging</domain>
    <filters>
      <confidence>above_0.85</confidence>
      <recency>last_30_days</recency>
      <min_user_count>100</min_user_count>
    </filters>
    <return_fields>
      <field>message_templates_ranked_by_engagement</field>
      <field>optimal_send_times</field>
      <field>engagement_rate_predictors</field>
      <field>account_risk_indicators</field>
    </return_fields>
  </knowledge_query>
</gather>
```

**Quantifiable Success Criteria:**

Verification with measurable thresholds:

```xml
<verify>
  <success_criteria>
    <metric name="delivery_rate" threshold=">0.95" critical="true"/>
    <metric name="response_time" threshold="<2000ms" critical="false"/>
    <metric name="cost_per_message" threshold="<0.01" critical="false"/>
    <metric name="quality_score" threshold=">0.80" critical="true"/>
  </success_criteria>
  
  <verification_steps>
    <step>Check API response status == 200</step>
    <step>Verify message_id present in response</step>
    <step>Confirm delivery_timestamp exists and is recent</step>
    <step>Check no rate_limit_warning in headers</step>
    <step>Calculate actual_cost and compare to estimate</step>
  </verification_steps>
  
  <on_failure>
    <if metric="delivery_rate" below_threshold="true">
      <action>retry with exponential backoff</action>
      <max_retries>3</max_retries>
      <backoff_multiplier>2.0</backoff_multiplier>
      <report_to>coordinator</report_to>
    </if>
    <if metric="cost_per_message" above_threshold="true">
      <action>switch to cheaper method (bash)</action>
      <report_to>knowledge_kiwi</report_to>
      <learning>tool more expensive than expected for this use case</learning>
    </if>
    <if metric="quality_score" below_threshold="true">
      <action>escalate to coordinator for manual review</action>
      <report_to>knowledge_kiwi</report_to>
    </if>
  </on_failure>
</verify>
```

**Cost Tracking Profile:**

```xml
<cost_profile>
  <agent name="profile_researcher">
    <model>claude-opus-4</model>
    <calls_per_run>10</calls_per_run>
    <tokens_per_call>2000</tokens_per_call>
    <estimated_cost_per_run>0.50</estimated_cost_per_run>
    <actual_cost_history>
      [0.48, 0.52, 0.49, 0.51, 0.47, 0.53, 0.50, 0.49, 0.51, 0.48]
    </actual_cost_history>
    <cost_variance>low</cost_variance>
    <cost_per_qualified_profile>0.005</cost_per_qualified_profile>
  </agent>
  
  <total_campaign_estimate>
    <coordinator>0.10</coordinator>
    <researcher>0.50</researcher>
    <senders>0.90</senders>
    <monitor>0.15</monitor>
    <total>1.65</total>
    <cost_per_successful_message>0.017</cost_per_successful_message>
    <roi_if_3_leads_at_150_each>271.4</roi_if_3_leads_at_150_each>
  </total_campaign_estimate>
</cost_profile>
```

**Benefits:**
- Decision trees are **machine-readable and optimizable**
- Knowledge queries are **standardized and cacheable**
- Success criteria are **measurable and comparable**
- Costs are **transparent and ROI-calculable**
- Reasoning patterns can be **discovered and improved** via registry
- Directives can be **ranked by cost-efficiency** across domains

---

### 2. Script Kiwi: Unix-First Composability

**Current State:**
Scripts execute directives. Not clear how they reason.

**Enhanced State:**
Scripts are building blocks for agent reasoning loops.

**Example:**
```bash
# Script: get_instagram_profile_stats.sh
# Used by: profile_researcher agent's <think> phase

TARGET_PROFILE=$1
API_KEY=$2

# Agent reasoning: "Should I use API or scraping?"
# Script KiwiWILL provides both options

# Option 1: API (if available)
get_via_api() {
    curl -H "Authorization: Bearer $API_KEY" \
         https://api.instagram.com/v1/users/search?q=$TARGET_PROFILE \
    | jq '.data[] | {username, followers, engagement_rate}'
}

# Option 2: Bash scraping (if API fails)
get_via_bash() {
    curl -s "https://www.instagram.com/$TARGET_PROFILE/?__a=1" \
    | jq '.graphql.user | {username: .username, followers: .edge_followed_by.count}'
}

# Agent decides which to use based on context
if [ "$METHOD" = "api" ]; then
    get_via_api
else
    get_via_bash
fi
```

**Benefits:**
- Scripts provide both "tool" and "bash" options
- Agents can choose based on availability/reliability
- Scripts are composable Unix primitives
- Reusable across directives

**Categories in Script Kiwi:**
- `tools/` - Single-purpose tool wrappers (Instagram API, etc)
- `primitives/` - Bash composables (curl, jq, grep, etc)
- `workflows/` - Multi-step scripts combining tools and bash
- `libraries/` - Helper functions for reasoning and decision-making

---

### 3. Knowledge Kiwi: Bidirectional Learning

**Current State:**
Knowledge entries are static. One-way storage.

**Enhanced State:**
Knowledge entries inform agent reasoning, agents update knowledge.

**Bidirectional Flow:**
```
Agent discovers:
  "Instagram blocks after 50 DMs/day"
  
  ↓ (agent reports to)
  
Knowledge Kiwi entry: "instagram-rate-limits"
  
  ↓ (coordinator queries before spawning)
  
Master Agent:
  "Load rate limit from Knowledge Kiwi: 50 DMs/day"
  
  ↓ (coordinator applies)
  
Coordinator enforces:
  "Rate limit pool = 50 / number_of_agents"
```

**Knowledge Entry Format:**
```yaml
zettel_id: 042-instagram-dm-rate-limits
title: Instagram DM Rate Limits - Empirical Data
entry_type: api_fact
source: agent_learnings
updated: 2025-01-06

content: |
  ## Rate Limits
  - Individual accounts: 50 DMs/day
  - Business accounts: 200 DMs/day
  - New accounts: 20 DMs/day
  
  ## Discovery Process
  - User ID: 847 (instagram_campaign_orchestrator users)
  - Tested across: 6 months
  - Confidence: 97% (based on 47 account blocks)
  
  ## Actionable Insights
  - Use 1 agent per 50 DMs/day
  - Spread sends throughout day
  - Monitor for "action block" warnings
  
  ## Related Patterns
  - see: context_rotation_pattern.md
  - see: failure_recovery_strategies.md

links_to: [trading_rate_limit_patterns, context_rotation]
version_contributed_by: [user_123, user_456, user_789]
```

**Learning Loop:**
```
1. Agent executes task
2. Agent records outcome (success/failure)
3. Sends learning to Knowledge Kiwi
4. Coordinator aggregates across all agents
5. Knowledge entry updated with new data
6. Version bump reflects improvement
7. Next coordinator queries updated entry
8. System improves automatically
```

---

## 4. Agent Autonomy Within Constraints

### How It Works

**Master Coordinator Sets Bounds:**
```
"Profile_Researcher: Find 1,000 Instagram profiles matching criteria
  Constraint: Use only public data
  Constraint: Max 5 API calls per profile
  Budget: 2,000 API calls total"
```

**Agent Reasons Within Bounds:**
```
Profile_Researcher gathers:
  - Criteria (what to search for)
  - Constraints (no private data)
  - Budget (2,000 API calls)
  - Knowledge Kiwi insights (best search strategies)

Profile_Researcher thinks:
  - Strategy A: Direct search (high confidence, uses 2 calls/profile)
  - Strategy B: Exploratory search (lower confidence, uses 1 call/profile)
  - Which maximizes results within budget?
  
Profile_Researcher acts:
  - Decides: Strategy A (more accurate)
  - Executes: Search with 2 calls per profile
  - Monitors: Am I within budget?
  
Profile_Researcher verifies:
  - Got 1,000 profiles?
  - Used < 2,000 calls?
  - Quality meets threshold?
  
Result: Profile_Researcher autonomously optimizes within Master's constraints
```

**Benefits:**
- Master doesn't micromanage execution
- Agent adapts to situations
- Constraints prevent abuse
- Agent reasoning is verifiable and loggable

---

## 5. Error Recovery & Learning

### Pattern: Graceful Degradation with Learning

**Scenario:** DM Agent hits rate limit

```
DM Agent thinks:
  "I have 500 more messages to send, but Instagram is refusing sends"
  
Options:
  (a) Crash and fail
  (b) Wait and retry (but when?)
  (c) Reduce sending rate
  (d) Switch to different method
  (e) Delegate to Master for decision

DM Agent chooses (e):
  Report to Master: "Rate limited, no budget remaining"
  
Master thinks:
  "It's day 1 of campaign. Limit is 50/day."
  "We hit it already. This account might be new?"
  "Options:"
  "  (a) Continue tomorrow (safe)"
  "  (b) Try business account endpoints (riskier)"
  "  (c) Switch to 1 agent instead of 3 (safer)"
  
Master consults Knowledge Kiwi:
  "New accounts hit limit after X messages"
  "Best recovery: pause and resume next day"
  
Master decides:
  "Pause DM senders. Resume tomorrow."
  
Master reports:
  To DM Agent: "Stop sending, resume tomorrow at 00:00 UTC"
  To Knowledge Kiwi: "Hit rate limit after 47 messages (new account?)"
  To Directive: "Consider reducing agent count for new accounts"
  
Next run:
  New agent uses Knowledge Kiwi: "Reduce to 1 agent for first week"
  System learns and improves
```

**Learning Captured:**
```yaml
zettel_id: 043-new-account-ramp-up
title: Instagram New Account Rate Limit Ramp-up
entry_type: learning

discovery:
  - Date: 2025-01-06
  - Agent: dm_sender (instagram_campaign_orchestrator v4.0)
  - User: orchestrator_user_847
  - Outcome: Hit rate limit after 47 messages (expected 50)

insight: |
  New Instagram accounts have:
  - Lower rate limits than mature accounts
  - Variable limits (47-50 messages observed)
  - Apparent internal throttling
  
pattern: |
  Week 1: 20 messages/day (safe)
  Week 2-4: 30 messages/day (safe)
  Week 4+: 50+ messages/day (safe)
  
recommendation: |
  - Detect account age from API response
  - Apply reduced rate limits for new accounts
  - Log all attempts to build confidence bands

related: [instagram_rate_limits, account_risk_detection]
```

---

## 5.5 Parallel Execution Semantics

**Problem:** Multiple agents must share resources without conflicts

**Structured Definition:**

```xml
<parallel_execution>
  <agent_group name="dm_sender" count="3">
    <spawn_strategy>simultaneous</spawn_strategy>
    
    <coordination>
      <shared_resources>
        <resource name="rate_limit">
          <pool_size>90</pool_size>
          <unit>messages_per_day</unit>
          <distribution_strategy>equal</distribution_strategy>
          <per_agent_allocation>30</per_agent_allocation>
          <enforcement>coordinator_validates_before_action</enforcement>
        </resource>
        
        <resource name="memory">
          <pool_size>2GB</pool_size>
          <distribution_strategy>dynamic</distribution_strategy>
          <min_per_agent>128MB</min_per_agent>
          <max_per_agent>512MB</max_per_agent>
        </resource>
      </shared_resources>
      
      <communication>
        <method>message_queue</method>
        <transport>coordinator_direct_call</transport>
        <heartbeat_interval>30s</heartbeat_interval>
        <timeout_before_replacement>300s</timeout_before_replacement>
      </communication>
      
      <work_distribution>
        <strategy>coordinator_assigns_batches</strategy>
        <batch_size>10</batch_size>
        <reassignment_on_failure>distribute_to_healthy_agents</reassignment_on_failure>
      </work_distribution>
    </coordination>
    
    <failure_handling>
      <detect>
        <method>heartbeat_timeout</method>
        <threshold>300s</threshold>
      </detect>
      <respond>
        <action>spawn_replacement_agent</action>
        <delay>10s</delay>
        <transfer_state>yes</transfer_state>
      </respond>
      <redistribute>
        <unfinished_work>distribute_to_remaining</unfinished_work>
        <backlog_priority>high</backlog_priority>
      </redistribute>
    </failure_handling>
    
    <observability>
      <metrics>
        <metric name="work_queue_depth"/>
        <metric name="messages_sent_per_agent"/>
        <metric name="error_rate_per_agent"/>
        <metric name="resource_utilization"/>
      </metrics>
      <logging>
        <level>info</level>
        <destinations>[knowledge_kiwi, coordinator]</destinations>
      </logging>
    </observability>
  </agent_group>
</parallel_execution>
```

**Registry Value:**
- Pattern proven across 1,247 Instagram campaigns
- Best distribution strategies for different task types
- Failure recovery times and reliability metrics
- Optimization history showing evolution

---

## 5.6 State Transfer Protocol

**Problem:** When agent reaches context limit, transfer state to fresh agent seamlessly

**Structured Format:**

```xml
<context_rotation>
  <trigger>
    <condition>agent.context_usage > 0.80</condition>
    <monitoring_interval>60s</monitoring_interval>
  </trigger>
  
  <state_transfer>
    <format>json</format>
    <schema>
      <required>
        <field name="current_task" type="object">
          {task_id, subtask_status, progress_percent}
        </field>
        <field name="pending_actions" type="array">
          List of next actions to execute
        </field>
        <field name="resource_state" type="object">
          {budget_remaining, rate_limit_quota, etc}
        </field>
      </required>
      <optional>
        <field name="full_history" type="array" compressed="true">
          Historical context for continuity
        </field>
        <field name="learned_patterns" type="object">
          Local learnings to share before terminating
        </field>
      </optional>
    </schema>
    <compression>gzip</compression>
    <size_limit>1MB</size_limit>
    <validation>
      <checksum>sha256</checksum>
      <on_corruption>reject_and_restart_task</on_corruption>
    </validation>
  </state_transfer>
  
  <handoff_procedure>
    <sequence>
      <step number="1">
        Agent detects 80% usage threshold
        Agent saves state to JSON
        Agent calculates checksum
        Agent signals coordinator: "ROTATION_READY"
      </step>
      <step number="2">
        Coordinator receives signal
        Coordinator spawns fresh agent
        Fresh agent initializes and reports: "READY_TO_RECEIVE"
      </step>
      <step number="3">
        Old agent transfers state to fresh agent
        Fresh agent loads state
        Fresh agent validates checksum
        Fresh agent confirms: "STATE_LOADED_VERIFIED"
      </step>
      <step number="4">
        Coordinator signals: "PROCEED_EXECUTION"
        Fresh agent resumes task from saved point
        Old agent documents final learnings
      </step>
      <step number="5">
        Old agent sends learnings to Knowledge Kiwi
        Old agent gracefully terminates
        Coordinator updates metrics: rotation successful
      </step>
    </sequence>
    
    <timing>
      <max_overlap_duration>30s</max_overlap_duration>
      <max_transition_time>5s</max_transition_time>
      <tolerance>zero_downtime</tolerance>
    </timing>
    
    <verification>
      <check>Fresh agent confirms task continuity</check>
      <check>No messages/actions lost in transfer</check>
      <check>Work output consistent before/after rotation</check>
      <fallback>If verification fails: restart task from checkpoint</fallback>
    </verification>
  </handoff_procedure>
  
  <learning_captured>
    <metric name="rotation_success_rate"/>
    <metric name="average_rotation_time"/>
    <metric name="context_usage_at_rotation"/>
    <metric name="state_transfer_size"/>
    <metric name="fresh_agent_warmup_time"/>
  </learning_captured>
</context_rotation>
```

**Registry Value:**
- State transfer patterns per agent type
- Successful rotation sequences from 2,847 uses
- Average rotation times and size metrics
- Failure recovery procedures tested

---

## 5.7 Reasoning Pattern Discovery & Search

**New Registry Capability:** Search by reasoning logic, not just domain

**Query Syntax:**

```xml
<!-- Search for directives with specific reasoning patterns -->
<registry_query>
  <search_type>reasoning_patterns</search_type>
  
  <pattern_match>
    <gather>
      <sources>api_data, knowledge_base</sources>
    </gather>
    <think>
      <decision_type>decision_tree</decision_type>
      <optimization_target>cost_efficient</optimization_target>
    </think>
    <act>
      <fallback_chain>tool → bash → code_gen</fallback_chain>
    </act>
    <verify>
      <includes>retry_on_failure</includes>
      <includes>learning_capture</includes>
    </verify>
  </pattern_match>
  
  <filters>
    <domain>social_media, trading, robotics</domain>
    <success_rate>min_0.85</success_rate>
    <user_count>min_50</user_count>
    <recency>last_6_months</recency>
  </filters>
  
  <return>
    <fields>
      <field>directive_name</field>
      <field>reasoning_loop_xml</field>
      <field>success_metrics</field>
      <field>cost_profile</field>
      <field>adaptation_history</field>
    </fields>
  </return>
</registry_query>
```

**What This Enables:**

**Pattern Transfer Across Domains:**
```
roboticist searches: "multiple agents, shared resource pool, parallel execution"
↓
Finds: instagram_campaign_orchestrator (social media)
         trading_multi_agent_system (financial)
         warehouse_robot_coordinator (robotics)
↓
All three use same reasoning pattern for shared resources
↓
Roboticist adopts pattern, adapts parameters for warehouse domain
↓
Creates: warehouse_robot_orchestrator.md v1.0
Publishes to registry with cross-references
```

**Reasoning Quality Evolution:**
```
v1.0 decision_tree: 3 branches, 45% success rate
v1.1 decision_tree: 5 branches, improved order, 78% success
v1.2 decision_tree: 7 branches, cost metrics, 89% success
v2.0 decision_tree: 12 branches, adaptive thresholds, 94% success

Registry shows improvement trajectory
Users can choose version based on stability vs cutting-edge
```

**Machine Learning on Patterns:**
```
Analyze 10,000 directives:
  - Which reasoning patterns correlate with high success?
  - Which decision orderings are most efficient?
  - Which failure recovery patterns are most resilient?
  - Which knowledge query filters work best?
  
Generate recommendations:
  - "For your task, directives using X pattern succeed 94% vs 76%"
  - "Decision order Y is 40% more cost-efficient than Z"
  - "Adding failure metric M predicts 18% higher reliability"
  
Suggest directives + reasoning improvements
```

---

## 6. Implementation Roadmap

### Phase 1: Reasoning Loop Infrastructure (Week 1-2)

**Goal:** Enable agents to use SDK-style reasoning

**Changes:**
- Update directive XML to include `<reasoning_loop>`
- Create reasoning loop executor in Context Kiwi
- Add gather/think/act/verify lifecycle logging

**Deliverables:**
- Directive format with reasoning components
- Reference implementation (Instagram example)
- Logging for reasoning steps

### Phase 2: Tool vs Bash Decision Framework (Week 3-4)

**Goal:** Agents autonomously choose execution mode

**Changes:**
- Create Script Kiwi categories: `tools/`, `primitives/`, `workflows/`
- Add decision logic templates to directives
- Implement tool/bash/code option provider

**Deliverables:**
- Script Kiwi reorganization
- Decision logic examples
- Tool registry with availability indicators

### Phase 3: Enhanced Knowledge Integration (Week 5-6)

**Goal:** Bidirectional learning between agents and Knowledge Kiwi

**Changes:**
- Add agent learning endpoints
- Create learning aggregation pipeline
- Update directives to query Knowledge Kiwi
- Version-tracking for learnings

**Deliverables:**
- Learning capture format
- Knowledge Kiwi query API
- Feedback loop examples

### Phase 4: Migration & Backwards Compatibility (Week 7-8)

**Goal:** Update existing directives, maintain compatibility

**Changes:**
- Migration tool: v3.x → v4.0
- Backwards compatibility layer
- Documentation and examples
- Community testing

**Deliverables:**
- Migration scripts
- Legacy adapter
- Updated examples

---

## 7. Practical Examples

### Example 1: Instagram Campaign (Simple)

**Directive:** `instagram_campaign_orchestrator_v4.md` (shown above)

**Key Integration Points:**
- Each agent has `<reasoning_loop>` with gather/think/act/verify
- Master coordinator orchestrates agent spawning
- Rate limit coordination shared via Master
- Learnings reported to Knowledge Kiwi
- Decision logic: when to use API vs bash

---

### Example 2: Trading System (Complex)

```xml
<directive name="trading_multi_agent_system" version="2.1.0">
  
  <coordinator_agent>
    <role>Portfolio manager with risk controls</role>
    
    <reasoning_loop>
      <gather>
        - Market data (prices, volumes)
        - Recent signal agent outputs
        - Risk manager constraints
        - Knowledge Kiwi: successful strategy patterns
      </gather>
      <think>
        - Which strategies are working best?
        - What's my capital allocation?
        - Risk manager approval required?
        - Should I rotate any agents?
      </think>
      <act>
        - Spawn signal agents (20)
        - Spawn execution agents (5)
        - Spawn risk manager (1)
        - Distribute capital budget
      </act>
      <verify>
        - Track P&L
        - Monitor risk metrics
        - Check agent health
        - Detect anomalies
      </verify>
    </reasoning_loop>
  </coordinator_agent>

  <sub_agents>
    <agent_group name="signal_generator">
      <count>20</count>
      
      <reasoning_loop>
        <gather>
          <data>Market prices, volumes</data>
          <knowledge>Best-performing strategies (from Knowledge Kiwi)</knowledge>
          <budget>Capital allocation from Master</budget>
        </gather>
        
        <think>
          <!-- SDK Pattern: Decide execution mode -->
          <decision>
            How should I generate signals?
            
            if strategy_is_simple:
              use tool (indicator API, already computed)
            elif strategy_is_complex:
              use code_gen (custom mathematical model)
            else:
              use bash (historical data processing)
          </decision>
        </think>
        
        <act>
          <!-- Agent autonomously selects execution -->
          <execution_mode>code_gen</execution_mode>
          <compute>
            Momentum strategy with regime filter
            (generated code optimized for speed)
          </compute>
          <output>signal (buy/sell/hold)</output>
        </act>
        
        <verify>
          <check>Signal generated?</check>
          <check>Computation time acceptable?</check>
          <recovery>If too slow, use simpler strategy next time</recovery>
          <learning>Log signal → actual outcome later</learning>
        </verify>
      </reasoning_loop>
    </agent_group>

    <agent_group name="execution_agent">
      <count>5</count>
      <coordination>
        <shared_capital_budget>1,000,000 USD</shared_capital_budget>
        <per_agent_limit>200,000 USD</per_agent_limit>
        <master_enforces>Yes</master_enforces>
      </coordination>
      
      <reasoning_loop>
        <gather>
          <signal>Buy/sell signal from signal agents</signal>
          <account_state>Cash, positions, P&L</account_state>
          <risk_constraints>From risk manager veto</risk_constraints>
          <knowledge>Best execution strategies</knowledge>
        </gather>
        
        <think>
          <decision>
            How should I execute?
            
            if large_order:
              use code_gen (VWAP algorithm, complex)
            elif time_sensitive:
              use tool (market order API, immediate)
            else:
              use bash (simple limit order script)
          </decision>
          
          <risk_check>
            Does this trade exceed my limit?
            Does risk manager approve?
            Am I within capital budget?
          </risk_check>
        </think>
        
        <act>
          <!-- Request permission from Master -->
          <ask_master>
            Trade: Buy 1000 shares at $50
            Capital needed: $50,000
            Remaining budget: $175,000
            Risk manager approval: pending
          </ask_master>
          
          <!-- Master checks -->
          <!-- Risk manager veto applied -->
          <!-- Capital constraint checked -->
          
          <execute_on_approval>
            method: market_order_api
            symbol: ABC
            quantity: 1000
            side: buy
          </execute_on_approval>
        </act>
        
        <verify>
          <check>Order filled?</check>
          <check>Fill price acceptable?</check>
          <recovery>
            if not_filled: cancel and retry with market order
            if poor_fill: log and adjust strategy next time
          </recovery>
          <learning>
            log execution quality (fill price vs expected)
            log slippage
            log execution time
          </learning>
        </verify>
      </reasoning_loop>
    </agent_group>

    <agent_group name="risk_manager">
      <count>1</count>
      <authority>veto_power</authority>
      
      <reasoning_loop>
        <gather>
          <positions>Current portfolio positions</positions>
          <pending_orders>Execution agents' proposed trades</pending_orders>
          <constraints>Risk limits, exposure limits, concentration limits</constraints>
          <knowledge>Risk incident patterns from Knowledge Kiwi</knowledge>
        </gather>
        
        <think>
          <analysis>
            If I approve this trade:
            - Will my portfolio concentration exceed limits?
            - Will leverage exceed policy?
            - Am I overexposed to any sector?
            - Does this match historical risk patterns?
          </analysis>
          
          <decision>
            approve | modify_and_approve | reject
          </decision>
        </think>
        
        <act>
          <!-- Risk manager veto -->
          <response>
            <trade>Buy 1000 ABC shares</trade>
            <decision>reject</decision>
            <reason>Already 35% in tech sector</reason>
            <suggestion>Limit to 500 shares or wait for sell</suggestion>
          </response>
        </act>
        
        <verify>
          <check>Did execution agent respect veto?</check>
          <check>Any risk metrics breached?</check>
          <recovery>
            if agent ignored veto:
              alert Master
              suspend agent temporarily
              investigate
          </recovery>
          <learning>
            Log risk incidents
            Log what strategies trigger vetoes
            Learn risk patterns
          </learning>
        </verify>
      </reasoning_loop>
    </agent_group>
  </sub_agents>

  <knowledge_integration>
    <signal_agents_report>
      - Which strategies work best (momentum, mean reversion, etc)
      - Performance metrics by market condition
      - Regime change indicators
    </signal_agents_report>
    
    <execution_agents_report>
      - Execution quality by market condition
      - Best execution methods (API vs algorithm)
      - Slippage patterns
    </execution_agents_report>
    
    <risk_manager_reports>
      - Risk incident patterns
      - What portfolio compositions trigger risk limits
      - Correlation between assets during stress
    </risk_manager_reports>
    
    <coordinator_reports>
      - Agent mix optimal for portfolio size
      - Allocation strategy (capital per agent)
      - Context rotation timing
    </coordinator_reports>
  </knowledge_integration>

</directive>
```

---

## 8. Design Principles

### 1. **Autonomy Within Bounds**
Agents reason and decide, Coordinator sets constraints.

### 2. **Explicit Over Implicit**
Reasoning loops, decision logic, and learnings are all explicit and versioned.

### 3. **Composable Primitives**
Unix-first: small scripts combine to enable agent flexibility.

### 4. **Bidirectional Learning**
Agents learn from Knowledge Kiwi, update it, improve it.

### 5. **Verifiable Reasoning**
Every agent decision is logged, auditable, improvable.

### 6. **Network Effects**
Each agent's learning improves all users' systems globally.

### 7. **Graceful Degradation**
Failures are learning opportunities, not crashes.

---

## 9. Migration Path for Existing Directives

### Current Directive (v3.x)
```xml
<directive name="some_workflow">
  <agent_architecture>
    <sub_agents>
      <agent name="worker"><directive>...</directive></agent>
    </sub_agents>
  </agent_architecture>
  <coordination_logic>...</coordination_logic>
</directive>
```

### Migrated Directive (v4.0)
```xml
<directive name="some_workflow" version="4.0.0">
  <!-- Backwards compat: keep v3 structure -->
  <agent_architecture>...</agent_architecture>
  <coordination_logic>...</coordination_logic>
  
  <!-- NEW: Add reasoning loops -->
  <coordinator_agent>
    <reasoning_loop>
      <gather>...</gather>
      <think>...</think>
      <act>...</act>
      <verify>...</verify>
    </reasoning_loop>
  </coordinator_agent>
  
  <sub_agents>
    <!-- Each agent gets reasoning loop -->
    <agent_group>
      <reasoning_loop>
        <gather>...</gather>
        <think><!-- Decision: tool vs bash vs code --></think>
        <act>...</act>
        <verify>...</verify>
      </reasoning_loop>
    </agent_group>
  </sub_agents>
  
  <!-- NEW: Knowledge integration -->
  <knowledge_integration>
    <agents_report_to>Knowledge Kiwi</agents_report_to>
    <learnings_captured>...</learnings_captured>
  </knowledge_integration>
</directive>
```

**Migration Tool:**
```bash
context-kiwi migrate instagram_campaign_orchestrator.md --to-v4

# Generates:
# - v4.0 structure
# - Placeholder reasoning loops
# - Migration checklist (what you need to add)
# - Examples from similar directives
```

---

## 10. Summary: The Integrated Model

| Aspect | Before (Pure Kiwi) | After (Integrated) | Benefit |
|---|---|---|---|
| **Agent reasoning** | Execute directive | Gather → think → act → verify | Clear decision framework |
| **Execution choice** | Directive specifies | Agent decides: tool/bash/code | Flexible, adaptive |
| **Knowledge flow** | One-way storage | Bidirectional | Continuous improvement |
| **Error handling** | Coordinator handles | Agent tries, Coordinator supervises | Better resilience |
| **Learning capture** | Manual | Automatic from agent decisions | Compounding knowledge |
| **Scalability** | Hierarchical agents | Hierarchical reasoning | Better control |
| **Reusability** | Patterns in registry | Patterns + reasoning loops + decisions | More transferable |

---

## 11. Why This Integration Matters

**Claude Agent SDK alone:**
- Great for single agent
- Hard to scale to multi-agent
- No knowledge sharing
- Each user reinvents orchestration
- Tool/bash decisions implicit

**Kiwi v3 alone:**
- Great for orchestration
- Hard to specify agent reasoning
- No tool/bash decision logic
- Orchestration patterns abstract
- Learning is manual

**Integrated v4:**
- ✅ Clear agent reasoning with **explicit decision trees**
- ✅ Autonomous tool/bash/code selection with **cost/success tradeoffs**
- ✅ Multi-agent orchestration proven at scale (50+ agents)
- ✅ **Bidirectional** knowledge sharing with automatic improvement
- ✅ Learning loops that improve system automatically
- ✅ Patterns transfer across domains via **reasoning pattern search**
- ✅ Parallel execution semantics **explicit and battle-tested**
- ✅ State transfer protocols ensuring **zero-downtime operation**
- ✅ Quantifiable success criteria enabling **objective comparison**
- ✅ Cost transparency with **ROI calculation**

**Compared to Gas Town (Mayor + Tmux):**

| Aspect | Gas Town | Integrated Kiwi |
|---|---|---|
| **Orchestration** | Locked in Mayor prompt | Versioned directives in global registry |
| **Reasoning** | Implicit in Claude's outputs | Explicit machine-readable decision trees |
| **Learning** | Lost when session ends | Captured in Knowledge Kiwi, improves future runs |
| **Patterns** | Trapped in one user's system | Global registry, semantically searchable |
| **Evolution** | Manual by author | Automatic through version history |
| **Portability** | Tied to Claude + tmux | Works with any agent runtime |
| **Cost tracking** | Implicit, hard to measure | Explicit per-agent profiles + ROI |
| **Decision logic** | Opaque | Inspectable, auditable, optimizable |
| **Failure recovery** | Ad-hoc error handling | Structured recovery procedures |
| **Network effects** | None (isolated) | Exponential (10,000+ users sharing) |

**Result:** "Orchestrated Reasoning" - systems that:
- **Think individually** (each agent has explicit reasoning loop)
- **Coordinate collectively** (shared resource management at scale)
- **Improve globally** (bidirectional knowledge flow via registry)
- **Evolve continuously** (decision trees refined through versions)
- **Transfer knowledge** (patterns discoverable across domains)
- **Compound in value** (each user's contribution improves everyone's)

---

## 12. Next Steps

1. **Create reference implementations** (Instagram, Trading examples)
2. **Update Context Kiwi directive format** to v4.0
3. **Reorganize Script Kiwi** into tools/primitives/workflows
4. **Enhance Knowledge Kiwi** with bidirectional learning
5. **Build migration tooling** for v3 → v4 upgrade
6. **Document reasoning loop patterns** for different domains
7. **Publish to community** for feedback and iteration
8. **Iterate based on real-world usage**
