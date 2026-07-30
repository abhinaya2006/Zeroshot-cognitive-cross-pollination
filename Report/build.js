const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageOrientation, LevelFormat, convertInchesToTwip, VerticalAlign,
  Header, Footer, PageNumber, NumberFormat
} = require("docx");
const fs = require("fs");

const FONT = "Times New Roman";
const COL_WIDTH_TOTAL = 9360; // usable width approx for letter w/ 1in margins minus gutter, per column ~4536 twips

// ---------- helpers ----------
function bodyPar(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 264 },
    indent: opts.noIndent ? {} : { firstLine: 260 },
    children: Array.isArray(text) ? text : [new TextRun({ text, font: FONT, size: 20 })],
    ...opts.paraProps,
  });
}

function run(text, o = {}) {
  return new TextRun({ text, font: FONT, size: o.size || 20, bold: !!o.bold, italics: !!o.italics, superScript: !!o.sup });
}

function heading(num, title) {
  return new Paragraph({
    spacing: { before: 260, after: 140 },
    keepNext: true,
    children: [new TextRun({ text: `${num}.  ${title.toUpperCase()}`, font: FONT, bold: true, size: 21 })],
  });
}

function subheading(text) {
  return new Paragraph({
    spacing: { before: 160, after: 80 },
    keepNext: true,
    children: [new TextRun({ text, font: FONT, bold: true, italics: true, size: 20 })],
  });
}

function caption(label, text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 200 },
    children: [new TextRun({ text: `${label}.  ${text}`, font: FONT, size: 18, bold: false })],
  });
}

function equation(text, num) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    tabStops: [{ type: "right", position: 4536 }],
    children: [
      new TextRun({ text: "        " + text, font: "Cambria Math", italics: true, size: 20 }),
      new TextRun({ text: `\t(${num})`, font: FONT, size: 20 }),
    ],
  });
}

function figurePlaceholder(label, desc, h = 2200) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 0 },
      border: {
        top: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
        bottom: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
        left: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
        right: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
      },
      children: [new TextRun({ text: "\n[ FIGURE PLACEHOLDER ]\n" + desc + "\n", font: FONT, italics: true, size: 18, color: "555555" })],
    }),
    caption(label, desc),
  ];
}

function bulletPar(text) {
  return new Paragraph({
    numbering: { reference: "bullet-list", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text, font: FONT, size: 20 })],
  });
}

function refPar(num, text) {
  return new Paragraph({
    spacing: { after: 100 },
    indent: { left: 260, hanging: 260 },
    children: [new TextRun({ text: `[${num}]  ${text}`, font: FONT, size: 18 })],
  });
}

// Table builder: header row + data rows, array of column widths (twips), total ~4536 for single column tables
function makeTable(headers, rows, widths) {
  const totalWidth = widths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: "auto", fill: "1F3864" },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 60, bottom: 60, left: 80, right: 80 },
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: h, font: FONT, bold: true, color: "FFFFFF", size: 17 })] })],
    })),
  });
  const dataRows = rows.map((r, ridx) => new TableRow({
    children: r.map((c, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: "auto", fill: ridx % 2 === 0 ? "FFFFFF" : "F2F2F2" },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 50, bottom: 50, left: 80, right: 80 },
      children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, children: [new TextRun({ text: String(c), font: FONT, size: 17 })] })],
    })),
  }));
  return new Table({ width: { size: totalWidth, type: WidthType.DXA }, columnWidths: widths, rows: [headerRow, ...dataRows] });
}

// ---------- content ----------

const titleBlock = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 160 },
    children: [new TextRun({ text: "Cognitive Cross-Pollination: A Structure-Mapping and Conceptual Blending Framework for Serendipitous Concept Recommendation", font: FONT, bold: true, size: 30 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: "Teja Abhinayasri Chakka", font: FONT, size: 22 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: "Department of Computer Science and Engineering, [RGUKT NUZVID]", font: FONT, italics: true, size: 19 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 280 },
    children: [new TextRun({ text: "[N210249]", font: FONT, italics: true, size: 19 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 280 },
    children: [
      new TextRun({ text: "Under the Guidance of: ", font: FONT, bold: true, size: 20 }),
      new TextRun({ text: "Mrs. Bhavani", font: FONT, size: 20 }),
    ],
  }),

];

const abstractBlock = [
  new Paragraph({
    spacing: { after: 80 },
    children: [new TextRun({ text: "Abstract—", font: FONT, bold: true, italics: true, size: 20 }),
    new TextRun({ text: "Conventional recommender systems optimize for relevance, engagement, or click-through probability, a design objective that reliably produces filter bubbles, popularity bias, and diminished long-term exploration. This paper presents the Cognitive Cross-Pollination Engine (CCPE), a zero-training recommendation framework that reframes discovery as a cognitive bridging problem rather than a similarity-ranking problem. Grounded in Structure-Mapping Theory and Conceptual Blending Theory, the system identifies scientific or academic concepts that are semantically distant from a user's declared hobby, then constructs a structural analogy that renders the unfamiliar concept intelligible in terms of the familiar domain. A locally computed sentence-embedding distance (all-MiniLM-L6-v2) governs candidate selection, a large language model (Groq-hosted Llama inference) performs zero-shot structure mapping and challenge generation, and an SQLite-backed cache reduces redundant inference calls. A rubric-based evaluator scores analogy quality and challenge responses, and an exponential-moving-average (EMA) learner model adapts future task difficulty. The system was evaluated across eight hobby categories using serendipity, semantic distance, analogy utility, challenge success rate, and system latency as evaluation criteria in place of classification accuracy. The best-performing configuration—an academic prompt variant operating at a far semantic-distance band with caching enabled—achieved a serendipity score of 0.65, an analogy utility of 0.83–0.88, a 73.3% challenge success rate, and an 85% latency reduction on cache hits. These results indicate that cognitively-grounded, analogy-mediated recommendation is a feasible and measurable alternative to similarity-based discovery.", font: FONT, size: 20 }),
    ],
  }),
  new Paragraph({
    spacing: { after: 220 },
    children: [
      new TextRun({ text: "Keywords—", font: FONT, bold: true, italics: true, size: 20 }),
      new TextRun({ text: "serendipitous recommendation; structure-mapping theory; conceptual blending; semantic distance; analogy generation; zero-shot learning; large language models; adaptive learning; recommender systems", font: FONT, italics: true, size: 20 }),
    ],
  }),
];

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullet-list",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 460, hanging: 260 } } } }],
    }],
  },
  styles: {
    default: { document: { run: { font: FONT, size: 20 } } },
  },
  sections: [
    // Section 1: title + abstract, single column, full width
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
        },
        column: { count: 1 },
      },
      children: [...titleBlock, ...abstractBlock],
    },
    // Section 2: remainder in two columns
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
        },
        column: { count: 2, space: 460 },
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16 })] })],
        }),
      },
      children: buildBody(),
    },
  ],
});

function buildBody() {
  const c = [];

  // 4. INTRODUCTION
  c.push(heading("I", "Introduction"));
  c.push(bodyPar("Recommender systems are the primary discovery mechanism for a large fraction of online content consumption, and their optimization objectives shape what users are exposed to over time. The dominant design paradigm—collaborative filtering, content-based filtering, hybrid recommendation, and their deep-learning variants—optimizes proxies for engagement such as click-through rate, watch time, or purchase probability. While effective at maximizing short-term interaction, this paradigm produces a well-documented set of side effects: filter bubbles, popularity bias, and a narrowing of the topics a user is ever exposed to. Diversification and exploration-exploitation techniques (e.g., multi-armed bandits) attempt to counteract this narrowing by injecting variety, but variety alone does not guarantee comprehension—a recommendation that is merely distant from a user's known interests can be as confusing as it is novel."));
  c.push(bodyPar("This paper introduces the Cognitive Cross-Pollination Engine (CCPE), a recommendation framework that treats novelty and comprehensibility as joint design constraints rather than competing objectives. Instead of ranking candidate items by learned similarity, CCPE selects a scientific or academic concept that is semantically distant from a user's declared hobby and then constructs a structural analogy that explains the unfamiliar concept using the vocabulary and relational structure of the familiar one. The system requires no supervised training, no domain-specific dataset, and no fine-tuning; it operates in a zero-shot setting using a pre-trained large language model (LLM) for structure mapping and a locally hosted sentence-embedding model for distance computation."));
  c.push(bodyPar("The remainder of this paper is organized as follows. Section II surveys related work in recommender systems and cognitive theories of analogy. Section III formalizes the problem statement, and Section IV discusses the motivating observations behind the design. Section V articulates the research gap. Sections VI–VIII describe the proposed methodology, system architecture, and detailed workflow. Section IX documents implementation details, Section X presents the mathematical formulation, and Section XI provides algorithmic pseudocode for the core modules. Sections XII–XIV describe the experimental setup, evaluation methodology, and results. Sections XV–XVII discuss limitations, future work, and conclusions."));

  // 5. RELATED WORK
  c.push(heading("II", "Related Work"));
  c.push(bodyPar("Classical recommender systems fall into three broad families: collaborative filtering, which infers preference from user–item interaction patterns; content-based filtering, which matches item features to a user profile; and hybrid approaches that combine both signals [3]. Knowledge-graph-based recommenders extend these approaches by traversing entity relationships to surface indirectly connected items, while diversification techniques re-rank candidate lists to reduce redundancy. Exploration–exploitation formulations, most commonly multi-armed bandits, allocate a fraction of recommendations to under-explored items to counteract over-specialization. Across all of these families, the underlying optimization target remains a behavioral proxy—clicks, dwell time, or conversion—rather than a measure of whether the user understood or learned from the recommended item."));
  c.push(bodyPar("A separate line of work in cognitive science addresses how humans acquire understanding of unfamiliar domains. Gentner's Structure-Mapping Theory (SMT) proposes that analogical reasoning proceeds by aligning the relational structure of a familiar base domain with an unfamiliar target domain, rather than by matching surface-level attributes [1]. Fauconnier and Turner's Conceptual Blending Theory extends this by describing how two input mental spaces can be selectively merged into a blended space that supports new inferences not present in either input alone [2]. These theories have long informed pedagogy and analogy generation in cognitive science but have not been widely operationalized as the core retrieval-and-explanation mechanism of a recommender system."));
  c.push(bodyPar("On the technical side, dense sentence embeddings such as Sentence-BERT and its distilled variant all-MiniLM-L6-v2 provide an efficient means of computing semantic similarity or distance between short text spans without requiring task-specific supervision [4]. The emergence of instruction-following LLMs, accessible through low-latency inference services, makes it practical to generate structured natural-language analogies on demand rather than through hand-authored templates. CCPE combines these two technical capabilities—local embedding-based distance computation and LLM-based zero-shot structure mapping—with SMT and Conceptual Blending Theory to operationalize cognitively-grounded serendipity as a recommendation objective."));

  // 6. PROBLEM STATEMENT
  c.push(heading("III", "Problem Statement"));
  c.push(bodyPar("Given a user-declared hobby or interest domain H, the problem addressed by this work is to identify a concept C from a disjoint knowledge domain such that (i) the semantic distance between H and C is large enough to constitute genuine novelty, (ii) C can be explained through a structurally valid analogy grounded in H, and (iii) the resulting explanation is verifiably comprehensible to the user, as measured by their ability to complete a generated application challenge. Formally, the system must solve a joint optimization over novelty and comprehensibility rather than treating them as separate post-hoc filters, and must do so without supervised training data linking hobbies to scientific concepts."));

  // 7. MOTIVATION
  c.push(heading("IV", "Motivation"));
  c.push(bodyPar("The motivation for this work originates from an observation about the trajectory of similarity-driven recommendation. A user who begins with an interest in, for example, bread baking is progressively guided toward bread recipes, then cake recipes, then pizza dough—each step a small semantic displacement from the last. Over many iterations, the user remains confined to a single knowledge cluster despite the cumulative distance traveled being nontrivial. Conversely, recommending a topic that is genuinely distant from bread baking—such as mycorrhizal fungal networks—without any bridging explanation produces cognitive overload rather than engagement, because no relational scaffold connects the two domains for the user."));
  c.push(bodyPar("Human cognition offers a resolution to this tension. People routinely come to understand unfamiliar systems through analogy: an electrical circuit is taught in terms of water flowing through pipes; the early planetary model of the atom borrowed its structure from the solar system. These are not surface-level resemblances but relational correspondences—flow, pressure, orbit, attraction—transferred from a well-understood base domain to a novel target domain. This observation motivates the central design principle of CCPE: rather than recommending content similar to what a user already knows, the system recommends content that is distant from what the user knows, and pairs it with an analogy that makes the distance traversable."));

  // 8. RESEARCH GAP
  c.push(heading("V", "Research Gap"));
  c.push(bodyPar("Existing recommender systems measure and optimize relevance; none of the surveyed approaches explicitly measure cognitive compatibility between a recommended item and a user's existing knowledge structure. Diversification techniques increase distributional variety but do not verify comprehensibility. Knowledge-graph recommenders can traverse to distant nodes but do not construct an explanatory bridge for the user. No reviewed system integrates Structure-Mapping Theory or Conceptual Blending Theory as an operational recommendation-and-explanation mechanism, and none evaluates recommendation quality using human-centered constructs such as analogy correctness, clarity, and structural consistency in place of, or alongside, engagement metrics. CCPE is positioned to close this gap: it requires no retraining, no domain-specific dataset, and uses structured reasoning over a pre-trained LLM rather than learned item-similarity."));

  // 9. PROPOSED METHODOLOGY
  c.push(heading("VI", "Proposed Methodology"));
  c.push(bodyPar("CCPE operationalizes two established cognitive theories as sequential computational stages. Structure-Mapping Theory governs the analogy-generation stage: given a base domain (the user's hobby) and a target domain (the distant concept), the system extracts the target's relational structure and re-expresses it using base-domain vocabulary and relations, rather than matching superficial attributes. Conceptual Blending Theory governs the challenge-generation stage: the hobby-space and the target concept-space are treated as two input mental spaces that are merged into a blended space, from which a concrete, solvable application task (the \"challenge\") is generated. Successful completion of the challenge by the user is treated as behavioral evidence that the blend—and therefore the underlying analogy—was cognitively effective."));
  c.push(subheading("A. Design Principles"));
  c.push(bulletPar("Zero-shot operation: no fine-tuning or task-specific training is performed; all analogy and challenge generation is delegated to a pre-trained, instruction-following LLM."));
  c.push(bulletPar("Local-first distance computation: semantic distance is computed on-device using a lightweight sentence-embedding model, avoiding a network round-trip and API cost for the discovery step."));
  c.push(bulletPar("Explainability by construction: because recommendations are mediated by an explicit analogy, the system's output is inherently explainable rather than requiring a separate post-hoc explanation module."));
  c.push(bulletPar("Adaptive personalization without model retraining: user mastery is tracked with a lightweight exponential-moving-average estimator rather than a trained personalization model, keeping the system stateless with respect to the LLM."));

  // 10. SYSTEM ARCHITECTURE
  c.push(heading("VII", "System Architecture"));
  c.push(bodyPar("The system architecture is organized as a linear pipeline in which each stage consumes the output of the previous stage and forwards a progressively refined artifact—from raw hobby text to a scored, adaptive learning interaction. Fig. 1 depicts the high-level pipeline."));
  figurePlaceholder("Fig. 1", "High-level system architecture of the Cognitive Cross-Pollination Engine, showing the eight-stage pipeline from user hobby input to adaptive learning update.").forEach(p => c.push(p));
  c.push(bodyPar("At the infrastructure level, the system is composed of a Next.js/Tailwind CSS front end, a FastAPI back end that orchestrates the pipeline, a Groq-hosted LLM for natural-language generation, a locally executed all-MiniLM-L6-v2 embedding model for semantic distance computation, and an SQLite database used as a response cache. The FastAPI layer is responsible for sequencing calls to the embedding model and the LLM, applying the cache-lookup logic, and returning a structured JSON payload to the front end for rendering."));

  // 11. DETAILED WORKFLOW
  c.push(heading("VIII", "Detailed Workflow"));
  figurePlaceholder("Fig. 2", "Detailed layer-by-layer workflow diagram illustrating data transformations between the Disrupter, Retrieval, Abstractor, Translator, Serendipity Evaluator, Challenge Generator, Rubric Grader, and EMA Adapter modules.").forEach(p => c.push(p));
  const layers = [
    ["Layer 1 — Semantic Distance Discovery (Disrupter)", "Input: user hobby string. Output: ranked list of candidate concepts at a target distance band. The module embeds the hobby using all-MiniLM-L6-v2, embeds a pool of candidate scientific/academic concepts, computes cosine distance for each pair, and filters candidates into near, mid, and far bands."],
    ["Layer 2 — Information Retrieval", "Input: selected candidate concept. Output: factual grounding text. The module queries external knowledge sources (Wikipedia API, arXiv API, DuckDuckGo Instant Answer API) to retrieve a factual description of the candidate concept, which is passed downstream to prevent hallucinated content in the analogy stage."],
    ["Layer 3 — Structure Mapping (Abstractor + Translator Agents)", "Input: hobby domain, target concept, retrieved facts. Output: a structured analogy. The Abstractor agent extracts the relational skeleton of the target concept (entities, relations, causal structure); the Translator agent re-expresses that skeleton using base-domain (hobby) vocabulary, producing a human-readable analogy."],
    ["Layer 4 — Serendipity Evaluation", "Input: analogy, semantic distance value. Output: a serendipity score combining unexpectedness and utility (Eq. 1). Analogies that are highly distant but rated low on comprehensibility are down-weighted relative to those that balance both factors."],
    ["Layer 5 — Challenge Generation", "Input: analogy. Output: a concrete application task requiring the user to apply the analogy (e.g., predicting an outcome, mapping an additional relation, or solving a small problem framed in hobby terms)."],
    ["Layer 6 — Rubric-Based Feedback", "Input: user's challenge response. Output: a graded score against a fixed rubric (correctness, clarity, structural consistency) plus qualitative feedback text, generated by the LLM acting as an automated grader."],
    ["Layer 7 — Adaptive Learning (EMA Adapter)", "Input: rubric score history. Output: an updated mastery estimate and an adjusted difficulty target for the next recommendation cycle, computed via an exponential moving average (Eq. 5–6)."],
  ];
  layers.forEach(([t, d]) => { c.push(subheading(t)); c.push(bodyPar(d)); });

  // 12. IMPLEMENTATION DETAILS
  c.push(heading("IX", "Implementation Details"));
  c.push(bodyPar("The implementation separates presentation, orchestration, and inference concerns across three tiers. Table I summarizes the technology stack and the role of each component within the pipeline."));
  c.push(makeTable(
    ["Layer", "Technology", "Role"],
    [
      ["Front end", "Next.js, Tailwind CSS", "User interaction, hobby input, challenge UI, feedback display"],
      ["Back end / orchestration", "FastAPI (Python)", "Pipeline sequencing, request validation, cache lookup"],
      ["LLM inference", "Groq API (Llama-family model)", "Structure mapping, analogy generation, challenge and rubric grading"],
      ["Semantic embedding", "all-MiniLM-L6-v2", "Local cosine-distance computation for candidate selection"],
      ["Caching", "SQLite", "Persisting prior analogy/challenge responses to avoid repeated API calls"],
    ],
    [1500, 1600, 1436]
  ));
  c.push(new Paragraph({ spacing: { after: 160 } }));
  c.push(bodyPar("The FastAPI orchestration layer exposes a single pipeline endpoint that internally sequences the seven functional modules described in Section VIII. Each module is implemented as an independent, stateless function that accepts a typed payload and returns a typed payload, which simplifies unit testing and allows any module to be replaced (e.g., substituting the embedding model or the LLM provider) without altering the surrounding pipeline logic. Caching is implemented as a key–value lookup keyed on the hash of (hobby, candidate concept, prompt variant); a cache hit bypasses both the retrieval and LLM-generation stages entirely, which is the dominant contributor to the latency reduction reported in Section XIV."));

  // 13. MATHEMATICAL FORMULATION
  c.push(heading("X", "Mathematical Formulation"));
  c.push(bodyPar("This section formalizes the core scoring and adaptation functions used throughout the pipeline."));
  c.push(subheading("A. Semantic Distance"));
  c.push(bodyPar("Given embedding vectors v_h and v_c for the hobby and candidate concept respectively, the semantic distance is computed as the complement of cosine similarity:"));
  c.push(equation("d(h,c) = 1 − ( v_h · v_c ) / ( ‖v_h‖ ‖v_c‖ )", "1"));
  c.push(subheading("B. Serendipity Score"));
  c.push(bodyPar("Following the standard unexpectedness × utility formulation, the serendipity score S combines the normalized semantic distance (unexpectedness) with a human- or rubric-derived utility rating:"));
  c.push(equation("S = Unexp(r) × U(r),   Unexp, U ∈ [0,1]", "2"));
  c.push(subheading("C. Analogy Utility"));
  c.push(bodyPar("Analogy quality is scored as a weighted combination of three rubric criteria—correctness, clarity, and structural consistency—each rated on a normalized 0–1 scale:"));
  c.push(equation("A = w1·Corr + w2·Clar + w3·Struct,  Σwi = 1", "3"));
  c.push(subheading("D. Challenge Success Rate"));
  c.push(bodyPar("Learning effectiveness is measured as the proportion of generated challenges solved correctly across N trials:"));
  c.push(equation("CSR = ( N_correct / N_total ) × 100%", "4"));
  c.push(subheading("E. Mastery Estimation (EMA)"));
  c.push(bodyPar("User mastery is tracked using an exponential moving average over successive rubric scores P_t, with smoothing factor α ∈ (0,1):"));
  c.push(equation("M_t = α·P_t + (1 − α)·M_(t−1)", "5"));
  c.push(subheading("F. Adaptive Difficulty Update"));
  c.push(bodyPar("The difficulty level offered at the next cycle is adjusted proportionally to the deviation of current mastery from a target threshold θ, scaled by a learning-rate parameter β:"));
  c.push(equation("D_(t+1) = D_t + β·( M_t − θ )", "6"));

  // 14. ALGORITHMS
  c.push(heading("XI", "Algorithms / Pseudocode"));
  c.push(subheading("Algorithm 1: Semantic Distance Discovery"));
  c.push(algoBlock([
    "Input: hobby string h, candidate pool C, target band b ∈ {near, mid, far}",
    "Output: ranked candidate list R",
    "1:  v_h ← Embed(h)",
    "2:  for each c in C do",
    "3:      v_c ← Embed(c)",
    "4:      d(h,c) ← 1 − CosineSimilarity(v_h, v_c)",
    "5:  end for",
    "6:  R ← Filter(C, d, band = b)",
    "7:  R ← SortDescending(R, key = d)",
    "8:  return R",
  ]));
  c.push(subheading("Algorithm 2: Structure-Mapping Analogy Generation"));
  c.push(algoBlock([
    "Input: hobby h, target concept c, retrieved facts F",
    "Output: analogy text A, serendipity score S",
    "1:  key ← Hash(h, c, promptVariant)",
    "2:  if CacheLookup(key) ≠ NULL then",
    "3:      return CacheLookup(key)",
    "4:  end if",
    "5:  structure ← LLM_Abstract(c, F)      // extract relational skeleton",
    "6:  A ← LLM_Translate(structure, h)     // map onto hobby vocabulary",
    "7:  rubric ← LLM_Rate(A)                // correctness, clarity, consistency",
    "8:  S ← Unexp(d(h,c)) × Utility(rubric)",
    "9:  CacheStore(key, (A, S))",
    "10: return (A, S)",
  ]));
  c.push(subheading("Algorithm 3: EMA-Based Adaptive Difficulty Update"));
  c.push(algoBlock([
    "Input: performance score P_t, previous mastery M_(t−1), α, β, θ, D_t",
    "Output: updated mastery M_t, next difficulty D_(t+1)",
    "1:  M_t ← α · P_t + (1 − α) · M_(t−1)",
    "2:  Δ ← M_t − θ",
    "3:  D_(t+1) ← D_t + β · Δ",
    "4:  D_(t+1) ← Clamp(D_(t+1), D_min, D_max)",
    "5:  return (M_t, D_(t+1))",
  ]));

  // 15. EXPERIMENTAL SETUP
  c.push(heading("XII", "Experimental Setup"));
  c.push(bodyPar("The system was evaluated across eight hobby categories spanning creative, technical, and physical domains (e.g., cooking, coding, music, and sports), each paired against a shared candidate pool of scientific and academic concepts drawn from the retrieval layer. All analogy and challenge generation used a Groq-hosted Llama-family model operating in zero-shot mode with no task-specific fine-tuning; semantic distance was computed locally using all-MiniLM-L6-v2 to avoid confounding embedding latency with LLM inference latency. The SQLite cache was toggled between enabled and disabled states to isolate its contribution to system latency and API-token consumption. Prompt variants (academic vs. conversational phrasing) and semantic-distance bands (near, mid, far) were treated as independent experimental factors, and each configuration was repeated ten times to assess output stability."));

  // 16. EVALUATION METHODOLOGY
  c.push(heading("XIII", "Evaluation Methodology"));
  c.push(bodyPar("Because CCPE optimizes for cognitive compatibility rather than click-through behavior, conventional recommender accuracy metrics (precision@k, recall@k, NDCG) are not applicable evaluation targets. Instead, the system is evaluated along six dimensions summarized in Table II, spanning novelty, explanation quality, learning outcome, and system efficiency."));
  c.push(makeTable(
    ["Category", "Evaluation Goal"],
    [
      ["Serendipity", "Are recommendations novel yet meaningful?"],
      ["Semantic distance", "How different is the discovered concept from the user's hobby?"],
      ["Analogy quality", "Is the generated analogy correct, clear, and structurally consistent?"],
      ["Learning effectiveness", "Can users successfully solve the generated challenge?"],
      ["System efficiency", "Does caching reduce latency and API usage?"],
      ["User adaptation", "Does the EMA-based learner model adjust difficulty over time?"],
    ],
    [1900, 2636]
  ));
  c.push(new Paragraph({ spacing: { after: 160 } }));
  c.push(bodyPar("The evaluation pipeline mirrors the production pipeline: each recommendation passes through analogy generation, challenge generation, rubric evaluation, and metric collection before aggregate performance analysis, ensuring that reported metrics reflect end-to-end system behavior rather than isolated module performance."));

  // 17. RESULTS AND DISCUSSION
  c.push(heading("XIV", "Results and Discussion"));
  c.push(bodyPar("Table III summarizes the seven quantitative metrics collected under the best-performing configuration (academic prompt variant, far semantic-distance band, caching enabled)."));
  c.push(makeTable(
    ["Metric", "Purpose", "Result"],
    [
      ["Serendipity score", "Unexpectedness × utility", "0.65"],
      ["Semantic distance", "Cosine distance (MiniLM)", "0.78"],
      ["Analogy utility", "Quality of generated analogy", "0.83"],
      ["Challenge success rate", "Learning effectiveness", "73.3%"],
      ["Pipeline latency (uncached)", "End-to-end response time", "4.82 s"],
      ["Pipeline latency (cached)", "Repeat-request response time", "0.72 s"],
      ["Average token usage", "Groq API efficiency", "2450 tokens/req."],
    ],
    [1750, 1550, 1236]
  ));
  c.push(new Paragraph({ spacing: { after: 160 } }));
  c.push(bodyPar("Table IV reports the outcome of the five controlled experiments described in Section XII."));
  c.push(makeTable(
    ["Experiment", "Objective", "Key Finding"],
    [
      ["Distance band (near/mid/far)", "Find optimal novelty level", "Far band achieved highest serendipity (0.65)"],
      ["SQLite cache on/off", "Measure latency & API savings", "85% latency reduction on repeat requests"],
      ["Prompt variants", "Compare prompting strategies", "Academic prompt yielded best analogy quality (0.88)"],
      ["Hobby categories", "Test generalization", "Consistent performance across 8 hobbies"],
      ["Repeated runs (10×)", "Measure stability", "Low variance in semantic distance (σ = 0.04)"],
    ],
    [1600, 1450, 1486]
  ));
  c.push(new Paragraph({ spacing: { after: 160 } }));
  figurePlaceholder("Fig. 3", "Bar chart comparing serendipity score across near, mid, and far semantic-distance bands, and pipeline latency with caching enabled versus disabled.").forEach(p => c.push(p));
  c.push(bodyPar("Two trends are noteworthy. First, serendipity peaked at the far distance band rather than at an intermediate band, suggesting that within the tested range, the structure-mapping stage was able to preserve comprehensibility even at high semantic distance—provided a valid analogy could be constructed—rather than novelty and clarity trading off as they typically do in unmediated diversification approaches. Second, caching reduced latency by roughly an order of magnitude (4.82 s to 0.72 s) with no measurable degradation in analogy quality, since cached responses are exact replays of previously validated LLM output rather than re-generations; this confirms that the SQLite layer is a low-risk, high-return optimization for repeat or shared hobby–concept pairs. The academic prompt variant outperforming the conversational variant on analogy utility (0.88 vs. an unreported lower baseline) suggests that formal, precise phrasing better constrains the LLM toward structurally faithful analogies than casual phrasing, which is consistent with prior findings that prompt specificity improves factual and structural fidelity in LLM generation."));

  // 18. LIMITATIONS
  c.push(heading("XV", "Limitations"));
  c.push(bulletPar("Evaluation relies substantially on LLM-based rubric grading rather than independent human raters at scale; systematic bias in the grading model could inflate reported analogy-quality and challenge-success figures."));
  c.push(bulletPar("The candidate concept pool and hobby set used for evaluation, while spanning eight categories, is not exhaustive; generalization to arbitrary hobbies and highly technical scientific domains remains untested."));
  c.push(bulletPar("The system depends on a third-party hosted LLM (Groq), introducing latency and availability characteristics outside the system's direct control, and API-side model updates could shift analogy quality without corresponding changes to the local codebase."));
  c.push(bulletPar("The EMA-based adaptation model is a lightweight heuristic rather than a learned personalization model; it may converge slowly or sub-optimally for users with highly irregular performance patterns."));
  c.push(bulletPar("No large-scale user study has yet been conducted; reported results reflect controlled experimental runs rather than longitudinal, real-world usage."));

  // 19. FUTURE WORK
  c.push(heading("XVI", "Future Work"));
  c.push(bulletPar("Conduct a user study with a larger and more demographically varied participant pool to validate analogy comprehensibility and challenge difficulty against human judgment rather than LLM-based grading alone."));
  c.push(bulletPar("Integrate the framework into educational platforms as a supplementary discovery and explanation layer alongside existing curricula."));
  c.push(bulletPar("Explore reinforcement-learning-based difficulty adaptation as a replacement for, or complement to, the current EMA heuristic."));
  c.push(bulletPar("Extend candidate retrieval to multimodal knowledge sources (diagrams, video, structured datasets) to enrich the structure-mapping stage beyond text."));
  c.push(bulletPar("Develop personalized, long-term learning paths that sequence multiple hobby–concept bridges over time rather than treating each recommendation cycle independently."));

  // 20. CONCLUSION
  c.push(heading("XVII", "Conclusion"));
  c.push(bodyPar("This paper presented the Cognitive Cross-Pollination Engine, a recommendation framework that replaces similarity-based ranking with cognitively-grounded analogy construction, drawing on Structure-Mapping Theory and Conceptual Blending Theory. The system operates in a zero-shot, zero-training regime, combining local semantic-embedding-based distance computation with LLM-based structure mapping, challenge generation, and rubric grading, and uses an SQLite cache to substantially reduce inference latency and cost. Evaluated across eight hobby categories using serendipity, semantic distance, analogy utility, challenge success rate, and system-efficiency metrics, the framework demonstrated that far-band semantic distance can be paired with high analogy quality when mediated by explicit structure mapping, and that caching yields an 85% latency reduction with no loss of output quality. These findings support cognitively-grounded, explanation-mediated recommendation as a measurable and practically deployable alternative to conventional engagement-optimized recommender systems, while also identifying clear directions—larger-scale user studies, reinforcement-learning-based adaptation, and multimodal retrieval—for strengthening the framework's evaluation rigor and real-world applicability."));

  // 21. REFERENCES
  c.push(heading("XVIII", "References"));
  c.push(refPar(1, "D. Gentner, \"Structure-mapping: A theoretical framework for analogy,\" Cognitive Science, vol. 7, no. 2, pp. 155–170, 1983."));
  c.push(refPar(2, "G. Fauconnier and M. Turner, The Way We Think: Conceptual Blending and the Mind's Hidden Complexities. New York, NY, USA: Basic Books, 2002."));
  c.push(refPar(3, "F. Ricci, L. Rokach, and B. Shapira, Eds., Recommender Systems Handbook, 2nd ed. New York, NY, USA: Springer, 2015."));
  c.push(refPar(4, "N. Reimers and I. Gurevych, \"Sentence-BERT: Sentence embeddings using Siamese BERT-networks,\" in Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP-IJCNLP), Hong Kong, China, 2019, pp. 3982–3992."));
  c.push(refPar(5, "Groq Inc., \"Groq API Documentation,\" 2024. [Online]. Available: https://console.groq.com/docs"));
  c.push(refPar(6, "Wikimedia Foundation, \"MediaWiki Action API,\" 2024. [Online]. Available: https://www.mediawiki.org/wiki/API"));
  c.push(refPar(7, "Cornell University, \"arXiv API User's Manual,\" 2024. [Online]. Available: https://arxiv.org/help/api"));
  c.push(refPar(8, "DuckDuckGo, \"DuckDuckGo Instant Answer API,\" 2024. [Online]. Available: https://duckduckgo.com/api"));

  return c;
}

function algoBlock(lines) {
  return new Table({
    width: { size: 4536, type: WidthType.DXA },
    columnWidths: [4536],
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: 4536, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, color: "auto", fill: "F7F7F7" },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        children: lines.map(l => new Paragraph({
          spacing: { after: 40 },
          children: [new TextRun({ text: l, font: "Consolas", size: 17 })],
        })),
      })],
    })],
  });
}

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("CCPE_IEEE_Report.docx", buf);
  console.log("written");
}).catch(e => { console.error(e); process.exit(1); });

