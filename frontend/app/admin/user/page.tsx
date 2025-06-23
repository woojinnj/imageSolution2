"use client";
import { useEffect, useState } from "react";

interface User {
  id: string;
  password: string;
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [newId, setNewId] = useState("");
  const [newPw, setNewPw] = useState("");

  // 사용자 목록 로딩
  const loadUsers = () => {
    fetch("http://localhost:8000/admin/user")
      .then((res) => res.json())
      .then((data) => setUsers(data.users || []))
      .catch(console.error);
  };

  useEffect(() => {
    loadUsers();
  }, []);

  // 회원 추가
  const addUser = async () => {
    if (!newId || !newPw) {
      alert("아이디와 비밀번호를 입력하세요.");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: newId, password: newPw }),
      });

      const data = await res.json();
      if (res.ok) {
        alert("회원 추가 완료");
        setNewId("");
        setNewPw("");
        loadUsers();
      } else {
        alert("추가 실패: " + (data.detail || "알 수 없는 오류"));
      }
    } catch (err) {
      console.error(err);
      alert("서버 오류 발생");
    }
  };

  // 비밀번호 초기화
  const resetPassword = async (username: string) => {
    const ok = confirm(`정말 ${username}의 비밀번호를 0000으로 초기화하시겠습니까?`);
    if (!ok) return;

    try {
      const res = await fetch(`http://localhost:8000/admin/reset-password?username=${username}`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        alert(data.msg);
        loadUsers();
      } else {
        alert("초기화 실패: " + (data.detail || "알 수 없는 오류"));
      }
    } catch (err) {
      console.error(err);
      alert("서버 오류 발생");
    }
  };

  // 회원 삭제
  const deleteUser = async (username: string) => {
    const ok = confirm(`정말 ${username} 계정을 삭제하시겠습니까?`);
    if (!ok) return;

    try {
      const res = await fetch(`http://localhost:8000/admin/delete-user?username=${username}`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (res.ok) {
        alert(data.msg || "삭제 완료");
        loadUsers();
      } else {
        alert("삭제 실패: " + (data.detail || "알 수 없는 오류"));
      }
    } catch (err) {
      console.error(err);
      alert("서버 오류 발생");
    }
  };

  return (
    <main className="p-8 text-white bg-gray-900 min-h-screen">
      <h1 className="text-2xl font-bold mb-6">👥 회원 관리</h1>

      {/* 회원 추가 입력창 */}
      <div className="mb-6 flex gap-4">
        <input
          placeholder="새 아이디"
          value={newId}
          onChange={(e) => setNewId(e.target.value)}
          className="p-2 rounded bg-gray-800 border border-gray-600 text-white"
        />
        <input
          type="password"
          placeholder="비밀번호"
          value={newPw}
          onChange={(e) => setNewPw(e.target.value)}
          className="p-2 rounded bg-gray-800 border border-gray-600 text-white"
        />
        <button
          onClick={addUser}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          추가
        </button>
      </div>

      {/* 사용자 목록 테이블 */}
      <table className="w-full border-collapse border border-gray-500 text-sm">
        <thead className="bg-gray-800">
          <tr>
            <th className="border border-gray-500 px-4 py-2">번호</th>
            <th className="border border-gray-500 px-4 py-2">아이디</th>
            <th className="border border-gray-500 px-4 py-2">비밀번호</th>
            <th className="border border-gray-500 px-4 py-2">관리</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user, index) => (
            <tr key={user.id} className="hover:bg-gray-700">
              <td className="border border-gray-500 px-4 py-2 text-center">{index + 1}</td>
              <td className="border border-gray-500 px-4 py-2 text-center">{user.id}</td>
              <td className="border border-gray-500 px-4 py-2 text-center">{user.password}</td>
              <td className="border border-gray-500 px-4 py-2 text-center space-x-1">
                <button
                  onClick={() => resetPassword(user.id)}
                  className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs"
                >
                  초기화
                </button>
                <button
                  onClick={() => deleteUser(user.id)}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-xs"
                >
                  삭제
                </button>
              </td>
            </tr>
          ))}
          {users.length === 0 && (
            <tr>
              <td colSpan={4} className="text-center py-4 text-gray-400">
                사용자 정보 없음
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </main>
  );
}
