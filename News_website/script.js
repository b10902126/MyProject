const API_KEY = "fbadf949490745a58e685ce601152603";
let currentCategory = null;
let currentPage = 1;
let currentKeyword = null;
let isLoading = false;
let lastArticleCount = 0;

function fetchNews(searchWithKey) {
    if (isLoading) return;
    isLoading = true;

    let url;
    if (searchWithKey) {
        url =
            "https://newsapi.org/v2/everything?" +
            `q=${currentKeyword}&` +
            `apiKey=${API_KEY}&` +
            `page=${currentPage}`;
    } else {
        const category =
            currentCategory || document.getElementById("category").value;
        url =
            "https://newsapi.org/v2/top-headlines?" +
            "country=us&" +
            `category=${category}&` +
            `apiKey=${API_KEY}&` +
            `page=${currentPage}`;
    }

    fetch(url)
        .then((response) => {
            if (!response.ok) return;
            return response.json();
        })
        .then((data) => {
            const newsContainer = document.getElementById("news-container");
            if (currentPage === 1) {
                newsContainer.innerHTML = "";
            }

            const articlesWithImg = data.articles.filter(
                (article) => article.urlToImage
            );

            if (
                articlesWithImg.length === 0 ||
                articlesWithImg.length === lastArticleCount
            ) {
                displayNoMoreNews();
                return;
            }

            lastArticleCount = articlesWithImg.length;

            for (article of articlesWithImg) {
                const newItem = `
                <div class="one-news">
                    <div class="news-img">
                        <img src="${article.urlToImage}" alt="${article.title}">
                    </div>
                    
                    <div class="news-content" id="news-content">
                        <div class="info">
                            <h5>${article.source.name}</h5>
                            <span>|</span>
                            <h5>${article.publishedAt}</h5>
                        </div>
                        <h2>${article.title}</h2>
                        <p>${article.description}</p>
                        <a href="${article.url}" target="_blank">Read More</a>
                    </div>
                </div>
                `;

                newsContainer.innerHTML += newItem;
            }

            currentPage++;
            isLoading = false;
        })
        .catch((error) => {
            console.log("Error message: " + error);
            isLoading = false;
        });
}

function displayNoMoreNews() {
    const newsContainer = document.getElementById("news-container");
    newsContainer.innerHTML += "<p>No more news to load.</p>";
}

window.onscroll = function () {
    if (currentCategory === null && currentKeyword === null) return;

    if (
        window.innerHeight + window.scrollY >=
        document.body.offsetHeight - 10
    ) {
        if (currentKeyword) {
            fetchNews(true);
        } else {
            fetchNews(false);
        }
    }
};

document.getElementById("search-category").addEventListener("click", () => {
    const category = document.getElementById("category").value;
    if (category === "-") {
        alert("Please choose a category");
        return;
    }
    if (category === currentCategory) return;
    currentCategory = category;
    currentPage = 1;
    fetchNews(false);
});

document
    .getElementById("search-keyword")
    .addEventListener("click", function () {
        const keyword = document.getElementById("search-box").value;
        if (keyword === "") {
            alert("Please enter something");
            return;
        }
        if (keyword === currentKeyword) return;
        currentPage = 1;
        currentCategory = null;
        currentKeyword = keyword;
        fetchNews(true);
    });
