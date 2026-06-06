const byId = (id) => document.getElementById(id);

const heroes = JSON.parse(byId("heroes-data").textContent);
const roles = JSON.parse(byId("roles-data").textContent);
const draftConfig = JSON.parse(byId("draft-config-data").textContent);

const TEAM_LIMIT = Number(draftConfig.team_size);
const VISIBLE_RECOMMENDATIONS = Number(draftConfig.visible_recommendations);
const DEFAULT_TOP_POOL = Number(draftConfig.default_top_pool);
const MAX_BANS = Number(draftConfig.max_bans);
const RECOMMEND_URL = draftConfig.recommend_url;

const picks = { ally: [], enemy: [] };
const bannedHeroes = [];

let latestRecommendations = [];
let latestTopPool = DEFAULT_TOP_POOL;
let latestDraftScore = null;

const sideSelect = byId("side");
const rankSelect = byId("rank");
const allyInput = byId("ally-input");
const enemyInput = byId("enemy-input");
const banInput = byId("ban-input");
const allySuggestions = byId("ally-suggestions");
const enemySuggestions = byId("enemy-suggestions");
const banSuggestions = byId("ban-suggestions");
const allyChips = byId("ally-chips");
const enemyChips = byId("enemy-chips");
const banChips = byId("ban-chips");
const allyCount = byId("ally-count");
const enemyCount = byId("enemy-count");
const banCount = byId("ban-count");
const roleFilters = byId("role-filters");
const roleStatus = byId("role-status");
const message = byId("message");
const results = byId("results");
const recommendButton = byId("recommend-button");
const RECOMMEND_BUTTON_TEXT = recommendButton.textContent;
const clearBanButton = byId("clear-ban-button");
const freeRoleFilterButton = byId("free-role-filter-button");

const heroById = new Map(heroes.map((hero) => [hero.id, hero]));
const roleById = new Map(roles.map((role) => [role.id, role.name]));
