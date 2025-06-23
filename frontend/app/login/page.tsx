//login/page.tsx
"use client";

import { jwtDecode } from "jwt-decode";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { FaEye, FaEyeSlash } from "react-icons/fa";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [token, setToken] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    const router = useRouter();

    const handleLogin = async () => { //비동기
        const res = await fetch("http://localhost:8000/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await res.json();

        if (res.ok) {
            const token = data.access_token;
            setToken(token);
            localStorage.setItem("access_token",token);

        try {
          const decoded: any = jwtDecode(token);
          const isAdmin = decoded.role === "admin";

          localStorage.setItem("is_admin", isAdmin.toString());

          alert("로그인 성공!");
          router.push("/server_config");

        } catch (err) {
          console.error("JWT 디코딩 실패:", err);
          alert("로그인 성공했지만 권한 판별에 실패했습니다.");
          router.push("/server_config"); // fallback
        }

      } else {
        alert("로그인 실패: " + (data.detail || "오류 발생"));
      }
    };

    return (
        <div style={{
            height: "100vh",
            backgroundColor: "#1E1F22",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            paddingTop: "50px"
        }}>
            <h1 style={{
                color: "#ffffff",
                fontSize: "48px",
                marginBottom: "30px",
                fontWeight: "bold",
                fontFamily: "Arial, sans-serif",
                letterSpacing: "2px"
            }}>
                SIGN IN
            </h1>

            <div style={{
                marginTop: "20px",
                padding: "25px",
                backgroundColor: '#2B2D30',
                borderRadius: "10px",
                width: "400px",
                textAlign: "center",
                fontSize: "18px"
            }}>
                {/* 아이디 입력창 */}
                <div style={{ position: "relative", width: "100%", marginBottom: "20px", paddingLeft:"5px" }}>
                    <input
                        type="text"
                        placeholder="아이디"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "10px 40px 10px 10px",
                            fontSize: "16px",
                            border: "2px solid #4A90E2",
                            borderRadius: "6px"
                        }}
                    />
                </div>

                {/* 비밀번호 입력창 */}
                <div style={{ position: "relative", width: "100%", marginBottom: "20px",paddingLeft:"5px" }}>
                    <input
                        type={showPassword ? "text" : "password"}
                        placeholder="비밀번호"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "10px 40px 10px 10px",
                            fontSize: "16px",
                            border: "2px solid #4A90E2",
                            borderRadius: "6px"
                        }}
                    />
                    <button
                        onClick={() => setShowPassword(prev => !prev)}
                        style={{
                            position: "absolute",
                            top: "50%",
                            right: "10px",
                            transform: "translateY(-50%)",
                            background: "transparent",
                            border: "none",
                            cursor: "pointer",
                            color: "#4A90E2",
                            fontSize: "18px"
                        }}
                    >
                        {showPassword ? <FaEyeSlash /> : <FaEye />}
                    </button>
                </div>

                {/* 로그인 버튼 */}
                <button
                    onClick={handleLogin}
                    style={{
                        backgroundColor: "#4A90E2",
                        color: "#fff",
                        padding: "11px 24px",
                        fontSize: "16px",
                        fontWeight: "bold",
                        border: "none",
                        borderRadius: "6px",
                        cursor: "pointer",
                        transition: "background-color 0.3s ease"
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = "#357ABD"}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = "#4A90E2"}
                >
                    로그인
                </button>
            </div>

            {/* 비밀번호 초기화 버튼 */}
            <button
                style={{
                    marginTop: "10px",
                    backgroundColor: "transparent",
                    color: "#999",
                    fontSize: "14px",
                    border: "none",
                    cursor: "pointer",
                }}
                onClick={() => router.push("/reset-password")}
            >
                비밀번호 초기화
            </button>
        </div>
    );
}
