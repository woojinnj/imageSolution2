"use client";

import { useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";
import { useRouter } from "next/navigation";

export default function AdminPage() {
  const [userRole, setUserRole] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      try {
        const decoded: any = jwtDecode(token);
        const role = decoded.role || "user";
        setUserRole(role);

        if (role !== "admin") {
          alert("접근 권한이 없습니다.");
          router.push("/server_config");
        }
      } catch (err) {
        console.error("JWT 오류:", err);
        router.push("/login");
      }
    } else {
      router.push("/login");
    }
  }, []);

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold mb-4">관리자 페이지</h1>

      {userRole === "admin" ? (
          <div>
              <ul className="list-disc ml-6 mt-4 space-y-2">
                  <li>
                      <button
                          onClick={() => router.push("/admin/user")}
                          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                          회원 관리 페이지로 이동
                      </button>
                  </li>
                <li>
                  <button
                      onClick={() => router.push("/admin/dbconnection")}
                      className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    DB 연결 관리 페이지로 이동
                  </button>
                </li>
                <li>DB 초기화 등</li>
              </ul>

          </div>
      ) : (
          <p>로딩 중...</p>
      )}
    </main>
  );
}
