// JavaScript để xử lý sự kiện tải ảnh lên và gọi API
const coffeeInput = document.getElementById("coffeeInput");
const coffeeImage = document.getElementById("coffeeImage");
const resultDiv = document.getElementById("result");
const reload = document.getElementById("captureInput");

function evaluateCoffee(imageFile) {
  // Gọi API để xử lý hình ảnh và nhận kết quả trả về
  // Giả định API endpoint là 'http://127.0.0.1:5000/predict'
  const formData = new FormData();
  formData.append("file", imageFile);

  fetch("http://127.0.0.1:5000/predict", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data) {
        resultDiv.textContent = `Dự đoán: ${data.data[0].class}, Tỷ lệ: ${data.data[0].confidence}`;
      } else {
        resultDiv.textContent = "Không thể đánh giá cà phê.";
      }
    })
    .catch((error) => {
      resultDiv.textContent = "Đã xảy ra lỗi khi gọi API.";
      console.error(error);
    });
}

coffeeInput.addEventListener("change", function (event) {
  const file = event.target.files[0];
  const reader = new FileReader();

  reader.onload = function (e) {
    coffeeImage.setAttribute("src", e.target.result);
    evaluateCoffee(file);
  };

  reader.readAsDataURL(file);
});

function reloadPage() {
  setTimeout(function() {
    window.location.reload();
  }, 1000);
  console.log("hi")
}

reload.addEventListener('click', reloadPage)