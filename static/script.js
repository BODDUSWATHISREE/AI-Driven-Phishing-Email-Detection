let pieChart = null;

const SAFE = "#22c55e";
const DANGER = "#ef4444";

async function predictEmail() {

    const email = document.getElementById("email").value.trim();

    if (email === "") {
        alert("Please paste an email first.");
        return;
    }

    document.getElementById("charCount").innerHTML = email.length;
    document.getElementById("wordCount").innerHTML =
        email.split(/\s+/).filter(Boolean).length;
    document.getElementById("urlCount").innerHTML =
        (email.match(/https?:\/\/|www\./gi) || []).length;

    try {

        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email })
        });

        const result = await response.json();
        const isPhishing = result.prediction === "Phishing";
        const color = isPhishing ? DANGER : SAFE;

        // Verdict banner
        const banner = document.getElementById("verdictBanner");
        banner.className = "verdict-banner " + (isPhishing ? "phishing" : "safe");
        document.getElementById("verdictIcon").innerHTML = isPhishing ? "🚨" : "✅";
        document.getElementById("prediction").innerHTML = isPhishing ? "Phishing" : "Legitimate";

        // Confidence
        let score = Math.round(result.probability * 100);
        const bar = document.getElementById("confidenceBar");
        bar.style.width = score + "%";
        bar.innerHTML = score + "%";
        bar.style.backgroundColor = color;

        // Gauge chart
        Plotly.newPlot("gauge", [{
            value: score,
            mode: "gauge+number",
            type: "indicator",
            title: { text: "Confidence Score" },
            gauge: { axis: { range: [0, 100] }, bar: { color } }
        }], {
            margin: { t: 40, b: 20, l: 20, r: 20 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            font: { color: "#1e293b" }
        }, {
            displayModeBar: false
        });

        // Pie chart
        if (pieChart) pieChart.destroy();
        pieChart = new Chart(document.getElementById("pieChart"), {
            type: "pie",
            data: {
                labels: ["Prediction", "Remaining"],
                datasets: [{
                    data: [score, 100 - score],
                    backgroundColor: [color, "#d9d9d9"],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: "bottom" } }
            }
        });

        // Recommendation
        document.getElementById("recommendation").innerHTML = isPhishing
            ? "⚠️ This email appears to be a phishing email. Avoid clicking links or downloading attachments."
            : "✅ This email appears to be legitimate and does not show phishing characteristics.";

    } catch (error) {
        console.log(error);
        alert("Prediction failed.");
    }
}