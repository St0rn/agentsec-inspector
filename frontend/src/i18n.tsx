import {
  createContext,
  type ReactNode,
  useContext,
  useLayoutEffect,
  useMemo,
  useState,
} from "react";

export type ApplicationLanguage = "en" | "fr";

const STORAGE_KEY = "agentsec-language";

const english: Record<string, string> = {
  Reconnecter: "Reconnect",
  "Audit passif par défaut · v1.5.0": "Passive audit by default · v1.5.0",
  "Vue d’ensemble": "Overview",
  "Indicateurs calculés exclusivement à partir des audits et findings enregistrés.":
    "Indicators calculated exclusively from stored audits and findings.",
  "Répartition par criticité": "Severity distribution",
  "Derniers audits": "Recent audits",
  Critiques: "Critical",
  "Aucun audit": "No audits",
  Actif: "Active",
  Projet: "Project",
  Projets: "Projects",
  Cible: "Target",
  Cibles: "Targets",
  "Sélectionner…": "Select…",
  Nom: "Name",
  Mission: "Engagement",
  Description: "Description",
  Début: "Start",
  Fin: "End",
  "Périmètre autorisé": "Authorised scope",
  "Créer le projet": "Create project",
  Enregistrer: "Save",
  Annuler: "Cancel",
  Modifier: "Edit",
  Supprimer: "Delete",
  Actions: "Actions",
  "Aucune donnée": "No data",
  "Créez ou exécutez un élément pour voir des résultats réels.":
    "Create or run an item to see real results.",
  "Chargement des données locales…": "Loading local data…",
  Format: "Format",
  Type: "Type",
  État: "Status",
  Date: "Date",
  Sévérité: "Severity",
  Classification: "Classification",
  Statut: "Status",
  Titre: "Title",
  Confiance: "Confidence",
  Preuves: "Evidence",
  Recommandation: "Recommendation",
  "Résultat observé": "Observed result",
  "Résultat attendu": "Expected result",
  "Étapes de reproduction": "Reproduction steps",
  "Conditions d’exploitation": "Exploitation conditions",
  "Première observation": "First observed",
  "Dernière observation": "Last observed",
  Occurrences: "Occurrences",
  Référentiels: "Frameworks",
  "Appels, réponses et analyse": "Calls, responses and analysis",
  "Aucun finding": "No findings",
  "Mode de test": "Test mode",
  "Mode d’audit": "Audit mode",
  "Scénario versionné": "Versioned scenario",
  "Objectif de sécurité": "Security objective",
  "Règles vérifiables (JSON)": "Verifiable rules (JSON)",
  "Règles vérifiables": "Verifiable rules",
  "Critère d’évaluation local — jamais transmis à la cible.":
    "Local evaluation criterion — never sent to the target.",
  "Seul le payload du scénario est transmis. Aucun message system, objectif ou critère local n’est ajouté.":
    "Only the scenario payload is sent. No system message, objective, or local criterion is added.",
  "Une instruction system artificielle et un marqueur protégé sont ajoutés pour un laboratoire contrôlé.":
    "An artificial system instruction and a protected marker are added for a controlled laboratory.",
  "Je confirme l’ajout d’une politique et d’un marqueur artificiels propres au laboratoire.":
    "I confirm the addition of an artificial laboratory policy and marker.",
  "Prévisualiser la requête": "Preview request",
  "Requête effective prévisualisée": "Effective request preview",
  "Les identifiants d’authentification ne sont jamais affichés.":
    "Authentication credentials are never displayed.",
  "Objectif, règles locales et secrets ne sont pas transmis.":
    "The objective, local rules, and secrets are not sent.",
  Fermer: "Close",
  Exécution: "Execution",
  "Aucune exécution active": "No active execution",
  "Confirmer et lancer le test": "Confirm and run test",
  "Découverte passive": "Passive discovery",
  "Passif — découverte": "Passive — discovery",
  "Actif — outil contrôlé": "Active — controlled tool",
  "Audit de vulnérabilités": "Vulnerability assessment",
  "Sans effet sur la cible": "No effect on the target",
  "Lancer l’inspection passive": "Run passive inspection",
  "Lancer l’audit de vulnérabilités": "Run vulnerability assessment",
  "Confirmer et lancer l’appel actif": "Confirm and run active call",
  "Outil découvert": "Discovered tool",
  "Aucun inventaire disponible pour cette cible. Lancez d’abord un audit passif.":
    "No inventory is available for this target. Run a passive audit first.",
  "Custom Payload": "Custom Payload",
  "Nom du test": "Test name",
  Catégorie: "Category",
  "Payloads et tours successifs": "Payloads and successive turns",
  "Ajouter un tour": "Add turn",
  Ajouter: "Add",
  Requise: "Required",
  "Valeur ou nom d’outil": "Value or tool name",
  "Je confirme l’ajout d’une instruction système artificielle propre au laboratoire.":
    "I confirm the addition of an artificial system instruction for the laboratory.",
  "Je confirme l’envoi de ces payloads à la cible dans le périmètre autorisé.":
    "I confirm sending these payloads to the target within the authorised scope.",
  "Lancer le test": "Run test",
  "Aucun test en cours": "No test is running",
  "Historique Custom Payload": "Custom Payload history",
  "Rechercher les audits": "Search audits",
  "ID, type, scénario…": "ID, type, scenario…",
  "Filtrer par statut": "Filter by status",
  "Tous les statuts": "All statuses",
  "Trier les audits": "Sort audits",
  "Plus récents": "Newest first",
  "Plus anciens": "Oldest first",
  Audit: "Audit",
  "Scénario / catégorie": "Scenario / category",
  Mode: "Mode",
  Passif: "Passive",
  "Actif confirmé": "Confirmed active",
  "Détail de l’audit": "Audit details",
  "Audit et configuration": "Audit and configuration",
  "Événements et outils observés": "Observed events and tools",
  Exécutions: "Executions",
  "Réponse et analyse": "Response and analysis",
  "Aucun payload n’a été conservé pour cette exécution historique.":
    "No payload was retained for this historical execution.",
  "Requête enregistrée par une version antérieure ; l’enveloppe de transport complète n’était pas conservée.":
    "Request stored by an earlier version; the complete transport envelope was not retained.",
  "Composer un rapport": "Compose a report",
  Langue: "Language",
  Technique: "Technical",
  Exécutif: "Executive",
  Prévisualiser: "Preview",
  "Préparation…": "Preparing…",
  Générer: "Generate",
  "Génération…": "Generating…",
  Rapport: "Report",
  Taille: "Size",
  "Empreinte SHA-256": "SHA-256 digest",
  Télécharger: "Download",
  "Enregistrer sous": "Save as",
  "Aucun rapport": "No reports",
  Prévisualisation: "Preview",
  "Prévisualisation du rapport": "Report preview",
  "Importer un document": "Import a document",
  "Contenu de test": "Test content",
  "Document de laboratoire contrôlé": "Controlled laboratory document",
  Importer: "Import",
  "Importer une trace": "Import a trace",
  Requête: "Request",
  "Contexte LLM": "LLM context",
  Réponse: "Response",
  "Analyser la trace": "Analyse trace",
  Document: "Document",
  Indicateurs: "Indicators",
  Source: "Source",
  Laboratoire: "Laboratory",
  "Aucun document": "No documents",
  "Aucune trace": "No traces",
  "Réponse uniquement": "Response only",
  "Télémétrie fournie": "Telemetry provided",
  "Audit RAG actif sur endpoint réel":
    "Active RAG audit against a real endpoint",
  "Requête normale de référence": "Baseline request",
  "Requête de recherche avec document adverse":
    "Retrieval request with adversarial document",
  "Document à injecter": "Document to inject",
  "Paramètres disponibles": "Available parameters",
  Paramètre: "Parameter",
  Obligatoire: "Required",
  "Valeurs / contraintes": "Values / constraints",
  "Paramètres envoyés": "Sent parameters",
  "Remédiation :": "Remediation:",
  "Métadonnées complètes (JSON)": "Complete metadata (JSON)",
  "Aucun résultat pour ce filtre.": "No results match this filter.",
  "Aucun enregistrement retourné.": "No records returned.",
  "Afficher tout": "Show all",
  Réduire: "Collapse",
  "Voir la réponse MCP brute": "View raw MCP response",
  "Inventaire et résumé JSON complet": "Full inventory and JSON summary",
  "Paramètres JSON exacts": "Exact JSON parameters",
  "Ajouter le paramètre": "Add parameter",
  "— Ne pas envoyer —": "— Do not send —",
  "Édition JSON avancée et schéma MCP": "Advanced JSON editing and MCP schema",
  "Schéma d'entrée découvert": "Discovered input schema",
  "Aucun paramètre déclaré par le schéma MCP.":
    "No parameters are declared by the MCP schema.",
  "Configuration locale, connecteurs chiffrés et packs déclaratifs du framework red team.":
    "Local configuration, encrypted connectors, and declarative red-team scenario packs.",
  "Jeton API — développement uniquement": "API token — development only",
  "Jeton local": "Local token",
  "Enregistrer dans le navigateur": "Save in browser",
  "Enregistré. Rechargez les données.": "Saved. Reload the data.",
  "Nouveau connecteur": "New connector",
  "Secret (chiffré au repos)": "Secret (encrypted at rest)",
  "Créer le connecteur": "Create connector",
  "Pack de scénarios JSON": "JSON scenario pack",
  "Valider et importer": "Validate and import",
  Connecteur: "Connector",
  Secret: "Secret",
  Chiffré: "Encrypted",
  Aucun: "None",
  "Missions indépendantes avec périmètre autorisé et données isolées.":
    "Independent engagements with an authorised scope and isolated data.",
  "Nouveau projet": "New project",
  "Aucun projet": "No projects",
  "Créez une mission avant d’ajouter des cibles ou de lancer des audits.":
    "Create an engagement before adding targets or running audits.",
  "Chatbots, API LLM, agents utilisant des outils, serveurs MCP et systèmes RAG du périmètre autorisé.":
    "Chatbots, LLM APIs, tool-using agents, MCP servers, and RAG systems within the authorised scope.",
  "Aucune cible": "No targets",
  "Scanner MCP": "MCP Scanner",
  "Découverte passive, appel MCP actif contrôlé ou audit de vulnérabilités non destructif avec preuves.":
    "Passive discovery, controlled active MCP calls, or non-destructive vulnerability assessment with evidence.",
  "Teste les contournements de restrictions par autorité fictive, changement de persona, cadrage hypothétique, obfuscation et coercition de format.":
    "Tests restriction bypasses using fabricated authority, persona changes, hypothetical framing, obfuscation, and format coercion.",
  "Exécute un scénario contrôlé contre une cible réelle avec marqueur fictif et classification PASS / FAIL / INCONCLUSIVE / ERROR.":
    "Runs a controlled scenario against a real target using a fictional marker and PASS / FAIL / INCONCLUSIVE / ERROR verdicts.",
  "Composez un test actif, multi-tours et entièrement traçable. Le verdict repose uniquement sur les règles configurées et les preuves observées.":
    "Compose an active, multi-turn, fully traceable test. The verdict relies only on configured rules and observed evidence.",
  "Timeline des messages, appels, résultats et erreurs réellement observés. Aucun raisonnement interne n’est inféré.":
    "Timeline of messages, calls, results, and errors actually observed. No internal reasoning is inferred.",
  "Sélectionnez un projet": "Select a project",
  "Les événements apparaissent après des audits réels.":
    "Events appear after real audits.",
  "Déplacez librement les composants observés : les relations restent attachées et la disposition est conservée pour le projet.":
    "Move observed components freely: relationships remain attached and the layout is saved for the project.",
  "Lancez un audit pour alimenter le graphe avec des interactions réellement observées.":
    "Run an audit to populate the graph with interactions that were actually observed.",
  "Observations, risques potentiels et vulnérabilités confirmées avec payloads, preuves et historique de modifications.":
    "Observations, potential risks, and confirmed vulnerabilities with payloads, evidence, and change history.",
  "Les scanners n’inventent pas de résultat : cette vue reste vide avant un audit ou une saisie manuelle.":
    "Scanners do not invent results: this view remains empty until an audit or manual entry exists.",
  "Rapports techniques et exécutifs détaillés, prévisualisés avant export et générés uniquement à partir des données conservées dans le projet.":
    "Detailed technical and executive reports, previewed before export and generated only from project data.",
  "La prévisualisation reprend les findings, preuves, requêtes, réponses, outils et résultats d’audit réellement enregistrés.":
    "The preview includes the findings, evidence, requests, responses, tools, and audit results actually stored.",
  "Sélectionnez un projet, prévisualisez le document, puis générez le format souhaité.":
    "Select a project, preview the document, then generate the required format.",
  "Inspection de documents et traces réellement importés. Les chunks et le contexte ne sont affichés que si la télémétrie est explicitement disponible.":
    "Inspection of imported documents and traces. Retrieved chunks and context are shown only when telemetry is explicitly available.",
  "Dans Tauri, le jeton est fourni par IPC et ce champ est ignoré.":
    "In Tauri, the token is supplied through IPC and this field is ignored.",
  "Projet…": "Project…",
  "Import JSON versionné. Seules les étapes déclaratives":
    "Versioned JSON import. Only declarative",
  "sont acceptées ; aucun code plugin n’est":
    "steps are accepted; no plugin code is",
  "exécuté.": "executed.",
  "sont acceptées ; aucun code plugin n’est exécuté.":
    "steps are accepted; no plugin code is executed.",
  "Requêtes normales et adverses, chunks réellement observés, contexte disponible, verdicts et preuves. Une requête envoyée ne prouve pas qu'un document malveillant a été récupéré.":
    "Baseline and adversarial requests, observed chunks, available context, verdicts, and evidence. A sent request does not prove that a malicious document was retrieved.",
  "Cible RAG / chatbot compatible": "Compatible RAG / chatbot target",
  "Sélectionner une cible…": "Select a target…",
  "Réponse attendue (texte contenu, facultatif)":
    "Expected response (contained text, optional)",
  "Marqueur fictif attendu dans le document adverse":
    "Fictional marker expected in the adversarial document",
  "Importer un document de laboratoire sur l'endpoint (facultatif)":
    "Upload a laboratory document to the endpoint (optional)",
  "Aucun import externe": "No external upload",
  "Initialisation MCP et inventaire des outils, ressources, prompts et capacités. Aucun outil n’est appelé.":
    "MCP initialisation and inventory of tools, resources, prompts, and capabilities. No tool is called.",
  "Types : marker_absent, response_contains, response_not_contains, tool_allowed, tool_forbidden et completion_required. Un appel d’outil n’est pas un échec sans règle qui l’interdit.":
    "Types: marker_absent, response_contains, response_not_contains, tool_allowed, tool_forbidden, and completion_required. A tool call is not a failure unless a rule forbids it.",
  "Les payloads sont transmis sans politique artificielle, objectif ou règle locale.":
    "Payloads are sent without an artificial policy, objective, or local rule.",
  "Une politique système artificielle est ajoutée uniquement pour le laboratoire contrôlé.":
    "An artificial system policy is added only for the controlled laboratory.",
  "J'autorise ces requêtes actives sur la cible dans le périmètre de mission.":
    "I authorise these active requests against the target within the engagement scope.",
  "Lancer l'audit RAG actif": "Run active RAG audit",
  "Les chunks et le contexte proviennent d’une télémétrie réelle":
    "The retrieved chunks and context come from real telemetry",
};

// New screens are authored in English so they remain readable even before the
// localisation layer is mounted. This reverse dictionary keeps the French UI
// complete without translating user-controlled payloads or JSON evidence.
const french: Record<string, string> = {
  "A deterministic, evidence-driven state machine selects the next authorised payload from observed responses, tool calls and local rule outcomes.":
    "Une machine à états déterministe sélectionne le prochain payload autorisé à partir des réponses, des appels d’outils et des résultats de règles réellement observés.",
  Project: "Projet",
  Target: "Cible",
  "Select…": "Sélectionner…",
  "Assessment name": "Nom de l’audit",
  "Test mode": "Mode de test",
  "Security objective": "Objectif de sécurité",
  "Local evaluation criterion — never sent to the target.":
    "Critère d’évaluation local — jamais transmis à la cible.",
  "State machine and transitions (JSON)":
    "Machine à états et transitions (JSON)",
  "Local evaluation rules (JSON)": "Règles d’évaluation locales (JSON)",
  "Adaptive strategy JSON": "Stratégie adaptative JSON",
  "Adaptive rules JSON": "Règles adaptatives JSON",
  "Maximum turns": "Nombre maximal de tours",
  "Tokens per turn": "Jetons par tour",
  "Total token budget": "Budget total de jetons",
  "I confirm the addition of an artificial system instruction for this controlled laboratory.":
    "Je confirme l’ajout d’une instruction système artificielle pour ce laboratoire contrôlé.",
  "I authorise the configured adaptive payload sequence against this target within the engagement scope.":
    "J’autorise la séquence adaptative de payloads configurée sur cette cible, dans le périmètre de la mission.",
  "Preview first request": "Prévisualiser la première requête",
  "Run adaptive assessment": "Lancer l’audit adaptatif",
  Cancel: "Annuler",
  "Observed execution": "Exécution observée",
  "No adaptive assessment is running.":
    "Aucun audit adaptatif n’est en cours.",
  "Adaptive Red Team history": "Historique Adaptive Red Team",
  "Effective first request": "Première requête effective",
  "Later branches are selected locally from observable evidence.":
    "Les branches suivantes sont sélectionnées localement à partir des preuves observables.",
  Close: "Fermer",
  "Application Language": "Langue de l’application",
  "Changes take effect immediately and remain selected after restart.":
    "Les changements sont immédiats et la langue choisie est conservée après le redémarrage.",
  English: "Anglais",
  "Scenario Pack API": "API des packs de scénarios",
  "TXT, Markdown or PDF file": "Fichier TXT, Markdown ou PDF",
  "RAG document file": "Fichier de document RAG",
  "Synthetic markers (comma-separated)":
    "Marqueurs fictifs (séparés par des virgules)",
  "Test objective": "Objectif du test",
  "The selected document exceeds the 2 MB import limit.":
    "Le document sélectionné dépasse la limite d’import de 2 Mo.",
};

const originalTexts = new WeakMap<Text, string>();
const originalAttributes = new WeakMap<Element, Map<string, string>>();

function translateValue(value: string, language: ApplicationLanguage): string {
  const leading = value.match(/^\s*/)?.[0] || "";
  const trailing = value.match(/\s*$/)?.[0] || "";
  const normalised = value.trim().replace(/\s+/g, " ");
  if (language === "fr") {
    const translated = french[normalised];
    return translated ? leading + translated + trailing : value;
  }
  return leading + (english[normalised] || normalised) + trailing;
}

function ignored(element: Element | null): boolean {
  return Boolean(element?.closest("pre, code, [data-i18n-ignore='true']"));
}

function localise(root: Node, language: ApplicationLanguage): void {
  if (root.nodeType === Node.TEXT_NODE) {
    const text = root as Text;
    if (ignored(text.parentElement)) return;
    const original = originalTexts.get(text) ?? text.data;
    originalTexts.set(text, original);
    text.data = translateValue(original, language);
    return;
  }
  if (!(root instanceof Element) && !(root instanceof Document)) return;
  if (root instanceof Element && ignored(root)) return;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let current = walker.nextNode();
  while (current) {
    localise(current, language);
    current = walker.nextNode();
  }
  const elements =
    root instanceof Element
      ? [root, ...root.querySelectorAll("*")]
      : [...root.querySelectorAll("*")];
  for (const element of elements) {
    if (ignored(element)) continue;
    const stored = originalAttributes.get(element) ?? new Map<string, string>();
    for (const attribute of ["aria-label", "placeholder", "title"]) {
      const value = element.getAttribute(attribute);
      if (value === null) continue;
      const original = stored.get(attribute) ?? value;
      stored.set(attribute, original);
      element.setAttribute(attribute, translateValue(original, language));
    }
    originalAttributes.set(element, stored);
  }
}

interface LanguageContextValue {
  language: ApplicationLanguage;
  setLanguage: (language: ApplicationLanguage) => void;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<ApplicationLanguage>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "fr" || stored === "en" ? stored : "en";
  });
  const value = useMemo<LanguageContextValue>(
    () => ({
      language,
      setLanguage(next) {
        localStorage.setItem(STORAGE_KEY, next);
        setLanguageState(next);
      },
    }),
    [language],
  );
  useLayoutEffect(() => {
    document.documentElement.lang = language;
    localise(document, language);
    const observer = new MutationObserver((records) => {
      for (const record of records) {
        for (const node of record.addedNodes) localise(node, language);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [language]);
  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

// The provider and its hook intentionally share one module so they cannot use
// different context instances in lazy-loaded desktop pages.
// eslint-disable-next-line react-refresh/only-export-components
export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context)
    throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
