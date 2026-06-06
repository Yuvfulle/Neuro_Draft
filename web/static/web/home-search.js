const normalize = (value) => String(value)
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^a-z0-9а-я]+/g, "");

const heroSearchIndex = [];
const heroByAlias = new Map();

function addSearchAlias(hero, alias) {
    const normalized = normalize(alias);
    if (!normalized) {
        return;
    }
    heroSearchIndex.push({ normalized, hero });
    if (!heroByAlias.has(normalized)) {
        heroByAlias.set(normalized, hero);
    }
}

heroes.forEach((hero) => {
    [hero.name, ...(hero.aliases || [])].forEach((alias) => {
        addSearchAlias(hero, alias);
    });
});

function levenshteinDistance(left, right) {
    const previous = Array.from({ length: right.length + 1 }, (_, index) => index);

    for (let leftIndex = 1; leftIndex <= left.length; leftIndex += 1) {
        const current = [leftIndex];
        for (let rightIndex = 1; rightIndex <= right.length; rightIndex += 1) {
            const insertCost = current[rightIndex - 1] + 1;
            const deleteCost = previous[rightIndex] + 1;
            const replaceCost = previous[rightIndex - 1]
                + (left[leftIndex - 1] === right[rightIndex - 1] ? 0 : 1);
            current.push(Math.min(insertCost, deleteCost, replaceCost));
        }
        previous.splice(0, previous.length, ...current);
    }

    return previous[previous.length - 1];
}

function closestHero(normalized) {
    if (normalized.length < 5) {
        return null;
    }

    let best = null;
    heroSearchIndex.forEach((entry) => {
        if (Math.abs(entry.normalized.length - normalized.length) > 2) {
            return;
        }
        const distance = levenshteinDistance(normalized, entry.normalized);
        if (!best || distance < best.distance) {
            best = { distance, hero: entry.hero };
        }
    });

    return best && best.distance <= 2 ? best.hero : null;
}

function prefixHeroes(normalized) {
    return heroSearchIndex
        .filter((entry) => entry.normalized.startsWith(normalized))
        .sort((left, right) => left.normalized.length - right.normalized.length)
        .map((entry) => entry.hero);
}

function findHero(value) {
    const normalized = normalize(value);
    if (!normalized) {
        return null;
    }

    return heroByAlias.get(normalized)
        || prefixHeroes(normalized)[0]
        || closestHero(normalized);
}

function matchingHeroes(value) {
    const normalized = normalize(value);
    if (!normalized) {
        return [];
    }

    const matches = [];
    const seen = new Set();

    function addMatch(hero) {
        if (hero && !seen.has(hero.id)) {
            matches.push(hero);
            seen.add(hero.id);
        }
    }

    addMatch(heroByAlias.get(normalized));
    prefixHeroes(normalized).forEach(addMatch);

    if (matches.length === 0) {
        addMatch(closestHero(normalized));
    }

    return matches.slice(0, 6);
}

function hideSuggestions(container) {
    container.classList.remove("visible");
    container.replaceChildren();
}

function heroSuggestionStatus(hero) {
    if (heroIsPicked(hero.id)) {
        return "выбран";
    }
    if (heroIsBanned(hero.id)) {
        return "бан";
    }
    return "";
}

function renderSuggestions(input, container) {
    const matches = matchingHeroes(input.value);
    container.replaceChildren();

    if (matches.length === 0) {
        container.classList.remove("visible");
        return;
    }

    matches.forEach((hero) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "suggestion";
        const status = heroSuggestionStatus(hero);

        const name = document.createElement("span");
        name.textContent = hero.name;
        button.appendChild(name);

        if (status) {
            const badge = document.createElement("span");
            badge.className = "suggestion-badge";
            badge.textContent = status;
            button.appendChild(badge);
            button.disabled = true;
        }

        button.addEventListener("mousedown", (event) => {
            event.preventDefault();
            if (button.disabled) {
                return;
            }
            input.value = hero.name;
            hideSuggestions(container);
        });
        container.appendChild(button);
    });

    container.classList.add("visible");
}
