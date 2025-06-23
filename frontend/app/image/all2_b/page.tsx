//page.tsx
"use client";
import React, {useEffect, useState, useRef} from "react";
import {jwtDecode} from "jwt-decode";

interface ImageItem {
    code: string;
    state: string;
    article_id: string;
    last_modified: string;
    article_data: any;
    has_image: boolean
    image_base64?: string;
}

export default function GalleryPage() {
    const [images, setImages] = useState<ImageItem[]>([]);
    const [selected, setSelected] = useState<ImageItem | null>(null);
    const [q, setQ] = useState("");
    const [aq, setAq] = useState("");
    const [status, setStatus] = useState("");
    const [page, setPage] = useState(1);
    const [perPage, setPerPage] = useState(10);
    const [total, setTotal] = useState(0);

    const [leftWidth, setLeftWidth] = useState(1000);
    const isDragging = useRef(false);

    const [userRole, setUserRole] = useState<string | null>(null);
    const [imageCache, setImageCache] = useState<{ [code: string]: string }>({});

    useEffect(() => {
        const token = localStorage.getItem("access_token"); // 또는 props/token/state에서 가져온 값
        if (token) {
            try {
                const decoded: any = jwtDecode(token);
                setUserRole(decoded.role || "user"); // role 없으면 일반 유저로 간주
            } catch (err) {
                console.error("JWT 디코딩 실패", err);
            }
        }
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging.current) {
                setLeftWidth(Math.min(Math.max(e.clientX, 800), 1400));
            }
        };

        const handleMouseUp = () => {
            isDragging.current = false;
        };

        window.addEventListener("mousemove", handleMouseMove);
        window.addEventListener("mouseup", handleMouseUp);

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", handleMouseUp);
        };
    }, []);

    const handleDisconnect = async () => {
        try {
            const res = await fetch("http://localhost:8000/disconnect_db", {
                method: "POST",
            });
            const json = await res.json();
            alert(json.message);
            window.location.href = "/server_config";
        } catch (err) {
            alert("접속 해제 실패");
        }
    };

    const fetchData = () => {
        fetch(
            `http://localhost:8000/api/image/list?q=${encodeURIComponent(q)}&aq=${encodeURIComponent(
                aq
            )}&status=${status}&page=${page}&per_page=${perPage}`
        )
            .then((res) => res.json())
            .then((data) => {
                console.log("서버 응답 내용:", data);
                setImages(data.results);
                setTotal(data.total);
            });
    };

    const fetchImage = async (code: string) => {
        if (imageCache[code]) return;  // 캐시에 있으면 생략

        try {
            const res = await fetch(`http://localhost:8000/api/image/by-code/${code}`)

            const data = await res.json();
            if (data.image_base64) {
                setImageCache(prev => ({...prev, [code]: data.image_base64}));
            }
        } catch (err) {
            console.error("이미지 로딩 실패:", err);
        }
    };

    useEffect(() => {
        fetchData();
    }, [q, aq, status, page, perPage]);

    const totalPages = Math.max(1, Math.ceil(total / perPage));

    return (

        <div className="flex h-screen overflow-hidden">
            {/* 왼쪽 패널 */}
            <div
                style={{width: `${leftWidth}px`}}
                className="flex flex-col h-full bg-gray-900 overflow-auto text-white"
            >
                <h1 className="text-xl font-bold mb-4">태그목록</h1>
                {/* 🔽 현재 권한 표시 */}
                <div className="text-sm text-gray-400 mb-4 px-2">
                    현재 권한:{" "}
                    <span className="font-semibold text-white">
              {userRole === "admin" ? "관리자" : "일반 사용자"}
            </span>
                </div>
                {/* 검색 필터 */}
                <div className="flex gap-2 mb-2 items-center">
                    <button className="border px-2 py-1" onClick={handleDisconnect}>
                        접속 끊기
                    </button>
                    <input
                        className="border px-2 py-1 bg-gray-800 text-white"
                        placeholder="Code"
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && setPage(1)}
                    />
                    <input
                        className="border px-2 py-1 bg-gray-800 text-white"
                        placeholder="Article"
                        value={aq}
                        onChange={(e) => setAq(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && setPage(1)}
                    />
                    <select
                        className="border px-2 py-1 bg-gray-800 text-white"
                        value={status}
                        onChange={(e) => {
                            setStatus(e.target.value);
                            setPage(1);
                        }}
                    >
                        <option value="">전체</option>
                        <option value="SUCCESS">SUCCESS</option>
                        <option value="TIMEOUT">TIMEOUT</option>
                        <option value="UNASSIGNED">UNASSIGNED</option>
                    </select>
                    <button className="border px-3" onClick={() => setPage(1)}>
                        검색
                    </button>
                </div>

                {/* 목록 테이블 */}
                <table className="w-full text-sm border-collapse text-white">
                    <thead>
                    <tr className="bg-gray-800">
                        <th className="border border-gray-600 px-2 text-center">Code</th>
                        <th className="border border-gray-600 px-2 text-center">State</th>
                        <th className="border border-gray-600 px-2 text-center">Article</th>
                        <th className="border border-gray-600 px-2 text-center">Modified</th>
                        <th className="border border-gray-600 px-2 text-center">Image</th>
                    </tr>
                    </thead>
                    <tbody>
                    {images.map((it) => (
                        <tr
                            key={it.code}
                            className={`cursor-pointer ${
                                selected?.code === it.code ? "bg-blue-900" : "hover:bg-gray-700"
                            }`}
                            onClick={() => {
                                setSelected(it)
                                fetchImage(it.code);
                            }}

                        >
                            <td className="border border-gray-600 px-2 text-center">{it.code}</td>
                            <td className="border border-gray-600 px-2 text-center">{it.state}</td>
                            <td className="border border-gray-600 px-2 text-center">{it.article_id}</td>
                            <td className="border border-gray-600 px-2 text-center">{it.last_modified}</td>
                            <td className="border border-gray-600 px-2 text-center">
                                {it.has_image ? "O" : "X"}
                            </td>
                        </tr>
                    ))}
                    {images.length === 0 && (
                        <tr>
                            <td colSpan={5} className="text-center p-4">
                                검색 결과 없음
                            </td>
                        </tr>
                    )}
                    </tbody>
                </table>
            </div>

            {/* 드래그 경계선 */}
            <div
                className="w-1 bg-gray-500 cursor-col-resize"
                onMouseDown={() => (isDragging.current = true)}
            ></div>

            {/* 오른쪽 패널 */}
            <div className="flex-1 p-4 overflow-auto bg-gray-800 text-white">
                {selected ? (
                    <>
                        <h2 className="font-bold mb-2">
                            {selected.code} ({selected.state})
                        </h2>

                        {selected?.has_image && imageCache[selected.code] ? (
                            <img
                                className="w-[300px] h-[300px] object-contain mb-2"
                                src={`data:image/jpeg;base64,${imageCache[selected.code]}`}
                                alt={selected.code}
                            />
                        ) : (
                            <div className="mb-2">이미지 없음</div>
                        )}

                        {selected.article_data !== "N/A" ? (
                            <>
                   <textarea
                       id="json-editor"
                       key={selected.code + selected.article_id}    // selected가 바뀔 때마다 새로 마운트
                       className="w-full h-80 border p-2 text-xs text-white"
                       defaultValue={JSON.stringify(selected.article_data, null, 2)}
                   />
                                {userRole === "admin" && (
                                    <button
                                        className="mt-2 px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                                        onClick={() => {
                                            const editedText = (document.getElementById("json-editor") as HTMLTextAreaElement).value;
                                            let articleData: any;
                                            try {
                                                articleData = JSON.parse(editedText);
                                            } catch {
                                                alert("JSON 형식이 잘못되었습니다.");
                                                return;
                                            }


                                            fetch("http://localhost:8000/articles", {
                                                method: "POST",
                                                headers: {"Content-Type": "application/json"},
                                                body: JSON.stringify({dataList: [articleData]})
                                            })
                                                .then(async res => {
                                                    if (res.ok) {
                                                        alert("저장 성공");
                                                        fetchData();       // 목록 갱신
                                                    } else {
                                                        const txt = await res.text();
                                                        alert(`저장 실패: ${txt || res.status}`);
                                                    }
                                                })
                                                .catch(err => {
                                                    console.error("저장 에러:", err);
                                                    alert("네트워크 오류로 저장하지 못했습니다.");
                                                });

                                        }}
                                    >
                                        저장
                                    </button>
                                )}
                            </>
                        ) : (
                            <div className="text-sm text-gray-400 mt-2">N/A</div>
                        )}


                    </>
                ) : (
                    <p className="text-gray-400">행을 클릭하면 상세 정보가 여기에 표시됩니다.</p>
                )}
            </div>


            {/* 하단 고정 페이지네이션 */}
            <div
                className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-gray-700 text-white rounded-lg shadow-lg px-6 py-2 z-50 flex items-center gap-4"
            >
                <button
                    className="px-2 py-1 text-2xl hover:bg-gray-600 rounded disabled:text-gray-400"
                    disabled={page === 1}
                    onClick={() => setPage(1)}
                >
                    «
                </button>
                <button
                    className="px-2 py-1 text-2xl hover:bg-gray-600 rounded disabled:text-gray-400"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                >
                    ‹
                </button>
                <span className="font-semibold text-sm whitespace-nowrap">
          페이지 <span className="text-blue-300">{page}</span> / {totalPages}
        </span>
                <select
                    className="bg-gray-600 border border-gray-400 px-2 py-1 rounded text-white text-sm"
                    value={perPage}
                    onChange={(e) => {
                        setPerPage(Number(e.target.value));
                        setPage(1);
                    }}
                >
                    {[...new Set([10, 20, 50, total])].map((n) => (
                        <option key={n} value={n}>
                            {n === total ? "전체" : `${n}개`}
                        </option>
                    ))}
                </select>
                <button
                    className="px-2 py-1 text-2xl hover:bg-gray-600 rounded disabled:text-gray-400"
                    disabled={page >= totalPages}
                    onClick={() => setPage(page + 1)}
                >
                    ›
                </button>
                <button
                    className="px-2 py-1 text-2xl hover:bg-gray-600 rounded disabled:text-gray-400"
                    disabled={page >= totalPages}
                    onClick={() => setPage(totalPages)}
                >
                    »
                </button>
            </div>
        </div>


    );


}
