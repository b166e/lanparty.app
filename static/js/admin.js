document.addEventListener("DOMContentLoaded", () => {
  const hostForm = document.getElementById("host-form")
  const searchInput = document.getElementById("search-users")
  const refreshBtn = document.getElementById("refresh-btn")

  // SSE for live updates
  const sse = new EventSource("/sse/admin")
  sse.onmessage = (e) => {
    if (e.data === "recargar") {
      location.reload()
    }
  }

  // Update host location
  if (hostForm) {
    hostForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const statusEl = document.getElementById("location-status")
      statusEl.textContent = "Updating location..."
      statusEl.className = "alert alert-info"

      try {
        navigator.geolocation.getCurrentPosition(
          async (pos) => {
            await fetch("/host", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
              }),
            })

            statusEl.textContent = "Location updated successfully!"
            statusEl.className = "alert alert-success"

            // Refresh user list without reloading the page
            if (refreshBtn) {
              refreshBtn.click()
            }

            // Clear message after 3 seconds
            setTimeout(() => {
              statusEl.textContent = ""
              statusEl.className = ""
            }, 3000)
          },
          (error) => {
            statusEl.textContent = `Error getting location: ${error.message}`
            statusEl.className = "alert alert-danger"

            // Clear message after 3 seconds
            setTimeout(() => {
              statusEl.textContent = ""
              statusEl.className = ""
            }, 3000)
          },
        )
      } catch (error) {
        statusEl.textContent = `Error: ${error.message}`
        statusEl.className = "alert alert-danger"

        // Clear message after 3 seconds
        setTimeout(() => {
          statusEl.textContent = ""
          statusEl.className = ""
        }, 3000)
      }
    })
  }

  // Filter user table
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      const query = this.value.toLowerCase()
      const table = document.getElementById("users-table")
      const rows = table.querySelectorAll("tbody tr")

      rows.forEach((row) => {
        const nombre = row.querySelector("td:first-child").textContent.toLowerCase()
        if (nombre.includes(query)) {
          row.style.display = ""
        } else {
          row.style.display = "none"
        }
      })
    })
  }

  // Refresh button functionality
  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      const usersTable = document.getElementById("users-table")
      const tbody = usersTable.querySelector("tbody")

      try {
        const response = await fetch("/api/users")
        const users = await response.json()

        // Clear table
        tbody.innerHTML = ""

        // Rebuild table with fresh data
        users.forEach((user) => {
          const tr = document.createElement("tr")
          tr.innerHTML = `
                        <td>${user.nombre}</td>
                        <td>${user.lat || "-"} / ${user.lon || "-"}</td>
                        <td>${user.distancia.toFixed(1)} m</td>
                        <td>
                            <form method="post" action="/enviar-html">
                                <input type="hidden" name="nombre" value="${user.nombre}">
                                <textarea name="html" rows="2" class="w-100 mb-2">${user.html || ""}</textarea>
                                <button type="submit" class="btn btn-primary">Guardar</button>
                            </form>
                        </td>
                    `
          tbody.appendChild(tr)
        })
      } catch (error) {
        console.error("Error refreshing user data:", error)
      }
    })
  }
})
