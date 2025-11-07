// 로그인
async function login() {
    const username = document.getElementById("login_id").value;
    const password = document.getElementById("login_pw").value;
  
    const response = await fetch("http://localhost:5000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const result = await response.json();
    if (result.success) {
      alert("로그인 성공!");
      localStorage.setItem("auto_login_token", result.token);
      location.href = "main.html";  // 로그인 후 메인화면으로
    } else {
      alert("로그인 실패");
    }
  }
  
async function signup() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const autoLoginChecked = document.getElementById("auto_login_checkbox").checked;
  
    // 회원가입 요청
    const signupRes = await fetch("http://localhost:5000/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
  
    const signupData = await signupRes.json();
  
    if (signupData.success) {
      // 자동으로 로그인
      const loginRes = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
  
      const loginData = await loginRes.json();
      if (loginData.success) {
        alert("회원가입 + 로그인 성공!");
  
        // 자동로그인 체크박스가 체크된 경우에만 토큰 저장
        if (autoLoginChecked) {
          localStorage.setItem("auto_login_token", loginData.token);
        }
  
        location.href = "map.html";  // 메인화면 이동
      } else {
        alert("자동 로그인 실패");
      }
    } else {
      alert(signupData.message);
    }
  }
  async function autoLogin() {
    const token = localStorage.getItem("auto_login_token");
    if (!token) return;
  
    const res = await fetch("http://localhost:5000/auto_login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token })
    });
  
    const result = await res.json();
    if (result.success) {
      alert(`${result.username}님 자동 로그인 완료`);
      // 필요한 로그인 후 처리
    } else {
      localStorage.removeItem("auto_login_token");
    }
  }
  
  
  
  // 친구 추가
async function addFriend() {
    const myUsername = document.getElementById("my_id").value;
    const friendUsername = document.getElementById("friend_id").value;
  
    const response = await fetch("http://localhost:5000/add_friend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ my_username: myUsername, friend_username: friendUsername })
    });
  
    const result = await response.json();
    if (result.success) {
      alert("친구 추가 성공!");
    } else {
      alert("친구 추가 실패: " + result.message);
    }
  }
  