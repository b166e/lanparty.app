document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form")
  const nombreInput = document.getElementById("nombre")
  const statusMessage = document.getElementById("status-message")

  // Get stored name
  const nombre = localStorage.getItem("nombre")

  // Setup SSE if name exists
  if (nombre) {
    nombreInput.value = nombre

    const evt = new EventSource(`/sse/usuario/${encodeURIComponent(nombre)}`)
    evt.onmessage = (e) => {
      if (e.data === "recargar") location.reload()
    }
  }

  // Handle form submission
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault()

      const nombre = nombreInput.value.trim()
      if (!nombre) {
        statusMessage.textContent = "Por favor ingresa tu nombre"
        statusMessage.className = "alert alert-warning"
        return
      }

      localStorage.setItem("nombre", nombre)

      // Show loading state
      statusMessage.textContent = "Obteniendo ubicación..."
      statusMessage.className = "alert alert-info"

      try {
        // Get coordinates
        const coords = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(
            (p) => resolve(p.coords),
            (err) => {
              console.error("Geolocation error:", err)
              resolve({ latitude: null, longitude: null })
            },
            { timeout: 10000 },
          )
        })

        statusMessage.textContent = "Enviando datos..."

        // Register user
        const response = await fetch("/registrar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nombre,
            lat: coords.latitude,
            lon: coords.longitude,
          }),
        })

        if (response.ok) {
          // Send screen dimensions
          await fetch("/pantalla", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              nombre,
              ancho: window.innerWidth,
              alto: window.innerHeight,
            }),
          })

          // Redirect to content view
          window.location.href = `/ver-html/${encodeURIComponent(nombre)}`
        } else {
          statusMessage.textContent = "Error al registrar usuario"
          statusMessage.className = "alert alert-danger"
        }
      } catch (error) {
        statusMessage.textContent = `Error: ${error.message}`
        statusMessage.className = "alert alert-danger"
      }
    })
  }
})
