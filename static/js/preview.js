document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("canvas")
  const fileInput = document.getElementById("background-image")
  const savePositionsBtn = document.getElementById("save-positions");

  const generateCropsBtn = document.getElementById("generate-crops")
  const statusMessage = document.getElementById("status-message")

  let offsetX = 0,
    offsetY = 0,
    dragTarget = null
  const positions = {}

  // Handle background image upload
  if (fileInput) {
    fileInput.addEventListener("change", async (e) => {
      const file = e.target.files[0]
      if (!file) return

      const formData = new FormData()
      formData.append("file", file)

      try {
        statusMessage.textContent = "Uploading image..."
        statusMessage.className = "alert alert-info"

        const response = await fetch("/upload-background", {
          method: "POST",
          body: formData,
        })

        const result = await response.json()

        if (result.status === "ok") {
          // Update background image without page reload
          canvas.style.backgroundImage = `url('/imagenes/fondo.jpg`
          statusMessage.textContent = "Background image updated successfully!"
          statusMessage.className = "alert alert-success"
        } else {
          statusMessage.textContent = "Error: " + result.mensaje
          statusMessage.className = "alert alert-danger"
        }
      } catch (error) {
        statusMessage.textContent = "Error uploading image: " + error.message
        statusMessage.className = "alert alert-danger"
      }

      // Clear after 3 seconds
      setTimeout(() => {
        statusMessage.textContent = ""
        statusMessage.className = ""
      }, 3000)
    })
  }

  // Drag and drop functionality
  if (canvas) {
    canvas.addEventListener("mousedown", (e) => {
      const el = e.target.closest(".pantalla")
      if (el && canvas.contains(el)) {
        dragTarget = el
        const rect = dragTarget.getBoundingClientRect()
        offsetX = e.clientX - rect.left
        offsetY = e.clientY - rect.top

        // Add active class for styling
        dragTarget.classList.add("dragging")
      }
    })

    document.addEventListener("mousemove", (e) => {
      if (dragTarget) {
        const contRect = canvas.getBoundingClientRect()
        const left = Math.max(0, e.clientX - contRect.left - offsetX)
        const top = Math.max(0, e.clientY - contRect.top - offsetY)

        // Make sure elements stay within the canvas
        const maxLeft = contRect.width - dragTarget.offsetWidth
        const maxTop = contRect.height - dragTarget.offsetHeight

        dragTarget.style.left = Math.min(left, maxLeft) + "px"
        dragTarget.style.top = Math.min(top, maxTop) + "px"

        // Update positions object
        const nombre = dragTarget.dataset.nombre
        positions[nombre] = {
          pos_x: Number.parseInt(dragTarget.style.left),
          pos_y: Number.parseInt(dragTarget.style.top),
        }
      }
    })

    document.addEventListener("mouseup", async (e) => {
      if (dragTarget) {
        dragTarget.classList.remove("dragging")
        dragTarget = null
      }
    })
  }

  // Save positions button
  if (savePositionsBtn) {

    savePositionsBtn.addEventListener("click", async () => {
      const pantallas = document.querySelectorAll('.pantalla');
      const canvasWidth = canvas.clientWidth;
      const canvasHeight = canvas.clientHeight;
  
      const positions = {};
      pantallas.forEach(p => {
          const id = p.dataset.id;
          const leftPx = parseFloat(p.style.left);
          const topPx = parseFloat(p.style.top);
          const xPercent = (leftPx / canvasWidth) * 100;
          const yPercent = (topPx / canvasHeight) * 100;
  
          positions[id] = {
              pos_x_percent: xPercent,
              pos_y_percent: yPercent
          };
      });
  
      const response = await fetch("/save-positions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ positions })
      });
  
      const result = await response.json();
      alert(result.mensaje);
  });
  
  }

  // Generate crops button
  if (generateCropsBtn) {
    generateCropsBtn.addEventListener("click", async () => {
      try {
        statusMessage.textContent = "Generating image crops..."
        statusMessage.className = "alert alert-info"

        const response = await fetch("/generar-recortes")
        const result = await response.json()

        if (result.status === "ok") {
          statusMessage.textContent = "Crops generated successfully!"
          statusMessage.className = "alert alert-success"
        } else {
          statusMessage.textContent = "Error: " + result.mensaje
          statusMessage.className = "alert alert-danger"
        }
      } catch (error) {
        statusMessage.textContent = "Error generating crops: " + error.message
        statusMessage.className = "alert alert-danger"
      }

      // Clear after 3 seconds
      setTimeout(() => {
        statusMessage.textContent = ""
        statusMessage.className = ""
      }, 3000)
    })
  }
})
