function currentDraftPayload() {
    return {
        ally_heroes: picks.ally.map((pick) => pick.id),
        ally_roles: picks.ally.map((pick) => pick.role),
        enemy_heroes: picks.enemy.map((pick) => pick.id),
        banned_heroes: [...bannedHeroes],
        side: sideSelect.value,
        avg_rank_tier: Number(rankSelect.value),
    };
}

async function requestRecommendations() {
    const response = await fetch(RECOMMEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentDraftPayload()),
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Ошибка API.");
    }
    return data;
}
