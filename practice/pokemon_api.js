function fetchData() {
    const pokemonName = document.getElementById("pokemonName").value;
    const url = `https://pokeapi.co/api/v2/pokemon/${pokemonName}`;
    fetch(url)
        .then((response) => {
            if (!response.ok) throw new Error("Couldn't find this pokemon");
            return response.json();
        })
        .then((data) => {
            const pokemonSpirte = data.sprites.front_default;
            const imgElement = document.getElementById("pokemonSpirte");
            imgElement.src = pokemonSpirte;
            imgElement.display = block;
        })
        .catch((error) => console.log(error));
}
