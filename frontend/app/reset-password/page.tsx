"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ResetPasswordPage() {
  const [username, setUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const router = useRouter();

  const handleReset = async () => {
    const res = await fetch("http://localhost:8000/auth/reset-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, new_Password: newPassword }),
    });

    const data = await res.json();

    if (res.ok) {
      alert("비밀번호가 성공적으로 변경되었습니다.");
      router.push("/login"); // 로그인 페이지로 이동
    } else {
        alert("변경 실패: " + (data.detail || JSON.stringify(data)));
    }
  };

  return (
    <div style={{ padding: "40px", maxWidth: "400px", margin: "100px auto", color: "#fff" }}>
      <h2>비밀번호 초기화</h2>
      <input
        type="text"
        placeholder="아이디"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        style={{ width: "100%", padding: "10px", marginBottom: "10px" }}
      />
      <input
        type="password"
        placeholder="새 비밀번호"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        style={{ width: "100%", padding: "10px", marginBottom: "10px" }}
      />
      <button
        onClick={handleReset}
        style={{
          width: "100%",
          padding: "10px",
          backgroundColor: "#4A90E2",
          color: "#fff",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer"
        }}
      >
        비밀번호 변경
      </button>
    </div>
  );
}
