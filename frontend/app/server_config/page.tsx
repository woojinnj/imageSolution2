"use client";

import {useState, useEffect} from "react";
import {jwtDecode} from "jwt-decode";

interface DBConnection {
    id: number;
    username: string;
    password: string;
    database: string;
    host: string;
    port: number;
    memo: string;
}

export default function ServerConfigPage() {
    const [host, setHost] = useState("");
    const [port, setPort] = useState("");
    const [userRole, setUserRole] = useState<string | null>(null);
    const [dbList, setDbList] = useState<DBConnection[]>([])
    const [dropdownFilter, setDropdownFilter] = useState("")
    // JWT 토큰에서 role 가져오기
    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (token) {
            try {
                const decoded: any = jwtDecode(token);
                setUserRole(decoded.role || "user");
            } catch (err) {
                console.error("JWT 디코딩 실패", err);
            }
        }
    }, []);

    // DB 목록 불러오기
    useEffect(() => {
        const fetchDbList = async () => {
            try {
                const res = await fetch("http://localhost:8000/admin/dbconnections");
                const data = await res.json();
                setDbList(data.dbconnections);
            } catch (err) {
                console.error("DB 목록 불러오기 실패", err);
            }
        };
        fetchDbList();
    }, []);

    const handleSubmit = async () => {
        const res = await fetch("http://localhost:8000/set_server", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({host, port}),
        });
        const data = await res.json();
        alert(data.message);
        if (data.status === "success") {
            window.location.href = "/image/all2_b";
        }
    };
    const filteredDbList = dbList.filter((db) =>
        [db.database, db.host, db.port,db.memo]
            .some((field) =>
                String(field ?? "")
                    .toLowerCase()
                    .includes(dropdownFilter.toLowerCase())
            )
    );
    return (
        <main style={{padding: "2rem"}}>
            <h1 className="text-2xl font-bold mb-4">DB 서버 설정</h1>

            {/* ── 검색용 입력 + 필터링된 드롭다운 ── */}
            <label className="block mb-1 font-semibold">DB 필터</label>
            <input
                type="text"
                placeholder="DB명, 호스트, 메모로 검색"
                value={dropdownFilter}
                onChange={(e) => setDropdownFilter(e.target.value)}
                className="mb-3 w-full md:w-96 px-2 py-1 border rounded"
            />

            <label className="block mb-2 font-semibold">DB 연결 선택</label>
            <select
                className="block mb-4 w-full md:w-96 px-2 py-1 border rounded"
                onChange={(e) => {
                    const selectedId = parseInt(e.target.value);
                    const selected = dbList.find((db) => db.id === selectedId);
                    if (selected) {
                        setHost(selected.host);
                        setPort(String(selected.port));
                    }
                }}
            >
                <option value="">-- DB를 선택하세요 --</option>
                {filteredDbList.map((db) => (
                    <option key={db.id} value={db.id}>
                        {db.database} ({db.host}:{db.port}) – {db.memo}
                    </option>
                ))}
            </select>

            {/* 연결 버튼 */}
            <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                disabled={!host || !port}
            >
                연결
            </button>

            {/* 관리자 전용 버튼 */}
            {userRole === "admin" && (
                <div className="mt-4">
                    <button
                        onClick={() => (window.location.href = "/admin")}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                        관리자 페이지로 이동
                    </button>
                </div>
            )}
        </main>
    );

}
