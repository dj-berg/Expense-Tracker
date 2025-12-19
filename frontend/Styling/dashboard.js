/* ======================================================
   DASHBOARD CHART SCRIPT
   Purpose: Render spending visualization from server data
   ====================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ==============================================
       CANVAS LOOKUP
       Purpose: Find the chart canvas on the page
       ============================================== */
    const canvas = document.getElementById("expenseChart");
    if (!canvas) return; // Exit if no chart is present

    /* ==============================================
       DATA EXTRACTION
       Purpose: Read category + amount data from HTML
       ============================================== */
    const categories = JSON.parse(canvas.dataset.categories);
    const amounts = JSON.parse(canvas.dataset.amounts);

    if (!categories.length || !amounts.length) return;

    /* ==============================================
       CHART INITIALIZATION
       Purpose: Create pie chart visualization
       ============================================== */
    const ctx = canvas.getContext("2d");

    new Chart(ctx, {
        type: "pie",
        data: {
            labels: categories,
            datasets: [{
                data: amounts
            }]
        },
        options: {
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
});
