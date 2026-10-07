function selectedResultRoleIds() {
    return new Set(
        [...roleFilters.querySelectorAll("input:checked")].map((input) => input.value)
    );
}

function scorePercent(value) {
    return Math.max(0, Math.min(Number(value) || 0, 100));
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#39;",
    }[char]));
}

function modelHeroChips(names) {
    return names.map((name) => (
        `<span class="model-chip">${escapeHtml(name)}</span>`
    )).join("");
}

function applyFreeRoleFilter() {
    const freeRoles = new Set(freeAllyRoles().map((role) => role.id));
    roleFilters.querySelectorAll("input").forEach((input) => {
        input.checked = freeRoles.has(input.value);
    });
    renderOutput();
}

function renderSkeletons() {
    results.replaceChildren();

    for (let index = 0; index < VISIBLE_RECOMMENDATIONS; index += 1) {
        const card = document.createElement("article");
        card.className = "result skeleton-card";
        card.innerHTML = `
            <div class="result-head">
                <div class="skeleton-line skeleton-mid"></div>
                <div class="skeleton-line skeleton-short"></div>
            </div>
            <div class="score-track"><span style="width: 64%"></span></div>
            <div class="skeleton-line skeleton-mid"></div>
            <div class="skeleton-line"></div>
        `;
        results.appendChild(card);
    }
}

function renderEmptyState() {
    results.replaceChildren();

    const empty = document.createElement("div");
    empty.className = "results-empty";
    empty.textContent = `Добавь героев и нажми «${RECOMMEND_BUTTON_TEXT}».`;
    results.appendChild(empty);
}

function renderOutput() {
    if (latestDraftScore) {
        renderDraftScore(latestDraftScore);
        return;
    }
    renderResults();
}

function renderDraftScore(data) {
    results.replaceChildren();
    roleStatus.textContent = `Полный драфт: ${TEAM_LIMIT * 2} / ${TEAM_LIMIT * 2}`;
    showMessage();

    const score = scorePercent(data.team_score);
    const card = document.createElement("article");
    card.className = "result draft-score";
    card.innerHTML = `
        <div class="result-head">
            <span>Оценка полного драфта твоей команды</span>
            <span class="score">${data.team_score}%</span>
        </div>
        <div class="score-track"><span style="width: ${score}%"></span></div>
        <div class="teams-line">Radiant: ${escapeHtml(data.radiant_team.join(", "))}</div>
        <div class="teams-line">Dire: ${escapeHtml(data.dire_team.join(", "))}</div>
        <div class="teams-line">Оценка Radiant: ${data.radiant_score}%</div>
        <div class="teams-line">${escapeHtml(data.score_note || "")}</div>
    `;
    results.appendChild(card);
}

function renderResults() {
    const selectedRoles = selectedResultRoleIds();
    const visibleItems = latestRecommendations
        .filter((item) => item.role_ids.some((roleId) => selectedRoles.has(roleId)))
        .sort((left, right) => right.score - left.score)
        .slice(0, VISIBLE_RECOMMENDATIONS);

    results.replaceChildren();

    if (latestRecommendations.length === 0) {
        renderEmptyState();
        return;
    }
    if (selectedRoles.size === 0) {
        showMessage("Выбери хотя бы одну роль в фильтрах.");
        return;
    }
    if (visibleItems.length === 0) {
        showMessage("Под выбранные фильтры нет героев в текущем топе.");
        return;
    }

    showMessage();
    visibleItems.forEach((item) => {
        const score = scorePercent(item.score);
        const hero = heroById.get(item.id);
        if (!hero) {
            return;
        }
        const recommendedRole = item.recommended_role || item.roles[0] || "";
        const recommendedRoleId = item.recommended_role_id || hero.roles[0];
        const card = document.createElement("article");
        card.className = "result";
        card.innerHTML = `
            <div class="result-head">
                <span class="result-name">${escapeHtml(item.name)}</span>
                <span class="score">${item.score}%</span>
            </div>
            <div class="score-track"><span style="width: ${score}%"></span></div>
            <div class="result-role">
                <span class="recommended-role">Роль: ${escapeHtml(recommendedRole)}</span>
                <span>Доступно: ${escapeHtml(item.roles.join(", "))}</span>
            </div>
            <div class="result-actions">
                <button class="secondary-button card-button" type="button" data-action="pick">Взять</button>
                <button class="secondary-button card-button ban-button" type="button" data-action="ban">В бан</button>
            </div>
            <details class="result-details">
                <summary>Как считалось</summary>
                    <div class="model-grid">
                        <div class="model-team">
                            <div class="model-team-head">
                                <span>Radiant</span>
                                <span>${item.target_side === "radiant" ? "кандидат" : "известно"}</span>
                            </div>
                            <div class="model-heroes">
                            ${modelHeroChips(item.radiant_team)}
                            </div>
                        </div>
                        <div class="model-team">
                            <div class="model-team-head">
                                <span>Dire</span>
                                <span>${item.target_side === "dire" ? "кандидат" : "известно"}</span>
                            </div>
                            <div class="model-heroes">
                            ${modelHeroChips(item.dire_team)}
                            </div>
                        </div>
                    </div>
                    <div class="model-meta">
                        <span>Оценка: ${item.score}%</span>
                        <span>Raw score: ${item.raw_score}</span>
                        <span>Пул: ${latestTopPool}</span>
                    </div>
                </details>
        `;
        card.querySelector('[data-action="pick"]').addEventListener("click", () => {
            addHeroToTeam("ally", hero, recommendedRoleId);
        });
        card.querySelector('[data-action="ban"]').addEventListener("click", () => {
            addBanByHero(hero);
        });
        results.appendChild(card);
    });
}

async function recommend() {
    showMessage();
    renderSkeletons();
    recommendButton.disabled = true;
    recommendButton.textContent = "Подбираю...";

    try {
        const data = await requestRecommendations();

        if (data.mode === "draft_score") {
            latestRecommendations = [];
            latestTopPool = 0;
            latestDraftScore = data;
            renderDraftScore(data);
            return;
        }

        latestDraftScore = null;
        latestRecommendations = data.recommendations;
        latestTopPool = data.top_pool;
        roleStatus.textContent = `${data.draft_status.summary} | пул: ${latestTopPool}`;
        renderResults();
    } catch (error) {
        latestRecommendations = [];
        latestDraftScore = null;
        renderOutput();
        showMessage(error.message || "Не удалось получить рекомендации.");
    } finally {
        recommendButton.disabled = false;
        recommendButton.textContent = RECOMMEND_BUTTON_TEXT;
    }
}
