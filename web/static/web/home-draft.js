function showMessage(text = "") {
    message.textContent = text;
}

function heroIsPicked(heroId) {
    return picks.ally.some((pick) => pick.id === heroId)
        || picks.enemy.some((pick) => pick.id === heroId);
}

function heroIsBanned(heroId) {
    return bannedHeroes.includes(heroId);
}

function usedRoles(type, exceptHeroId = null) {
    return new Set(
        picks[type]
            .filter((pick) => pick.id !== exceptHeroId)
            .map((pick) => pick.role)
    );
}

function freeAllyRoles() {
    const used = usedRoles("ally");
    return roles.filter((role) => !used.has(role.id));
}

function defaultRoleForHero(hero, type) {
    const used = usedRoles(type);
    return hero.roles.find((roleId) => !used.has(roleId)) || null;
}

function resetResults() {
    latestRecommendations = [];
    latestTopPool = DEFAULT_TOP_POOL;
    latestDraftScore = null;
    renderOutput();
}

function addHeroToTeam(type, hero, preferredRole = null) {
    if (!hero) {
        showMessage("Герой не найден.");
        return false;
    }
    if (heroIsPicked(hero.id)) {
        showMessage("Этот герой уже выбран.");
        return false;
    }
    if (heroIsBanned(hero.id)) {
        showMessage("Этот герой забанен.");
        return false;
    }
    if (picks[type].length >= TEAM_LIMIT) {
        const teamName = type === "ally" ? "В твоей команде" : "У противников";
        showMessage(`${teamName} уже ${TEAM_LIMIT} героев.`);
        return false;
    }

    const takenRoles = usedRoles(type);
    const role = preferredRole && hero.roles.includes(preferredRole) && !takenRoles.has(preferredRole)
        ? preferredRole
        : defaultRoleForHero(hero, type);

    if (!role) {
        showMessage(`${hero.name}: все доступные роли уже заняты.`);
        return false;
    }

    picks[type].push({ id: hero.id, role });
    showMessage();
    renderPicks();
    resetResults();
    return true;
}

function addHero(type) {
    const input = type === "ally" ? allyInput : enemyInput;
    const hero = findHero(input.value.trim());

    if (addHeroToTeam(type, hero)) {
        input.value = "";
    }
}

function removeHero(type, heroId) {
    picks[type] = picks[type].filter((pick) => pick.id !== heroId);
    renderPicks();
    resetResults();
}

function clearTeam(type) {
    picks[type] = [];
    renderPicks();
    resetResults();
}

function changePickRole(type, heroId, role) {
    const pick = picks[type].find((item) => item.id === heroId);
    const hero = heroById.get(heroId);
    if (!pick || !hero) {
        return;
    }
    if (!hero.roles.includes(role)) {
        showMessage(`${hero.name} не подходит под роль ${roleById.get(role)}.`);
        renderPicks();
        return;
    }
    if (usedRoles(type, heroId).has(role)) {
        showMessage("Эта роль уже выбрана в этой команде.");
        renderPicks();
        return;
    }

    pick.role = role;
    showMessage();
    renderPicks();
    resetResults();
}

function addBanByHero(hero) {
    if (!hero) {
        showMessage("Герой не найден.");
        return false;
    }
    if (bannedHeroes.length >= MAX_BANS) {
        showMessage(`В банах может быть не больше ${MAX_BANS} героев.`);
        return false;
    }
    if (heroIsPicked(hero.id)) {
        showMessage("Выбранного героя нельзя добавить в баны.");
        return false;
    }
    if (heroIsBanned(hero.id)) {
        showMessage("Этот герой уже в банах.");
        return false;
    }

    bannedHeroes.push(hero.id);
    showMessage();
    renderBans();
    resetResults();
    return true;
}

function addBan() {
    const hero = findHero(banInput.value.trim());

    if (addBanByHero(hero)) {
        banInput.value = "";
    }
}

function removeBan(heroId) {
    const index = bannedHeroes.indexOf(heroId);
    if (index >= 0) {
        bannedHeroes.splice(index, 1);
    }
    renderBans();
    resetResults();
}

function clearBans() {
    bannedHeroes.splice(0, bannedHeroes.length);
    renderBans();
    resetResults();
}

function renderPicks() {
    renderTeam("ally", allyChips);
    renderTeam("enemy", enemyChips);
    renderRoleStatus();
    allyCount.textContent = `${picks.ally.length} / ${TEAM_LIMIT}`;
    enemyCount.textContent = `${picks.enemy.length} / ${TEAM_LIMIT}`;
}

function renderRoleStatus() {
    const freeRoles = freeAllyRoles().map((role) => role.name);
    roleStatus.textContent = freeRoles.length
        ? `Свободные роли: ${freeRoles.join(", ")}`
        : "Все роли в твоей команде выбраны.";
}

function renderTeam(type, container) {
    container.replaceChildren();
    picks[type].forEach((pick) => {
        const hero = heroById.get(pick.id);
        if (!hero) {
            return;
        }

        const chip = document.createElement("div");
        chip.className = "chip";

        const name = document.createElement("span");
        name.textContent = hero.name;

        const roleSelect = document.createElement("select");
        roleSelect.className = "role-select";
        roleSelect.setAttribute("aria-label", `Роль ${hero.name}`);

        const unavailableRoles = usedRoles(type, hero.id);
        hero.roles.forEach((roleId) => {
            const option = document.createElement("option");
            option.value = roleId;
            option.textContent = roleById.get(roleId);
            option.disabled = unavailableRoles.has(roleId);
            roleSelect.appendChild(option);
        });

        roleSelect.value = pick.role;
        roleSelect.addEventListener("change", () => {
            changePickRole(type, hero.id, roleSelect.value);
        });

        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "×";
        button.setAttribute("aria-label", `Убрать ${hero.name}`);
        button.addEventListener("click", () => removeHero(type, hero.id));

        chip.append(name, roleSelect, button);
        container.appendChild(chip);
    });
}

function renderBans() {
    banChips.replaceChildren();
    banCount.textContent = `${bannedHeroes.length} / ${MAX_BANS}`;

    bannedHeroes.forEach((heroId) => {
        const hero = heroById.get(heroId);
        if (!hero) {
            return;
        }

        const chip = document.createElement("div");
        chip.className = "chip";

        const name = document.createElement("span");
        name.textContent = hero.name;

        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "×";
        button.setAttribute("aria-label", `Убрать бан ${hero.name}`);
        button.addEventListener("click", () => removeBan(hero.id));

        chip.append(name, button);
        banChips.appendChild(chip);
    });
}
