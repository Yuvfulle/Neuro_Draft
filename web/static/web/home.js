roleFilters.querySelectorAll("input").forEach((input) => {
    input.addEventListener("change", renderOutput);
});

document.querySelectorAll("[data-add]").forEach((button) => {
    button.addEventListener("click", () => addHero(button.dataset.add));
});

function setupHeroInput(input, suggestions, addCallback) {
    const refresh = () => renderSuggestions(input, suggestions);

    input.addEventListener("input", refresh);
    input.addEventListener("focus", refresh);

    input.addEventListener("blur", () => {
        setTimeout(() => hideSuggestions(suggestions), 120);
    });

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            const firstSuggestion = matchingHeroes(input.value)
                .find((hero) => !heroSuggestionStatus(hero));
            if (firstSuggestion) {
                input.value = firstSuggestion.name;
            }
            hideSuggestions(suggestions);
            addCallback();
        }
    });
}

setupHeroInput(allyInput, allySuggestions, () => addHero("ally"));
setupHeroInput(enemyInput, enemySuggestions, () => addHero("enemy"));
setupHeroInput(banInput, banSuggestions, addBan);

byId("add-ban-button").addEventListener("click", addBan);
byId("clear-ally-button").addEventListener("click", () => clearTeam("ally"));
byId("clear-enemy-button").addEventListener("click", () => clearTeam("enemy"));
clearBanButton.addEventListener("click", clearBans);
sideSelect.addEventListener("change", resetResults);
rankSelect.addEventListener("change", resetResults);
freeRoleFilterButton.addEventListener("click", applyFreeRoleFilter);
recommendButton.addEventListener("click", recommend);

renderPicks();
renderBans();
renderOutput();
