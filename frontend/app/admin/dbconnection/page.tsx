'use client'

import {useState, useEffect, useRef} from 'react'

interface DBConnection {
    id: number
    username: string
    password: string
    database: string
    host: string
    port: string
    memo: string
}

export default function DBConnectionPage() {
    const [connections, setConnections] = useState<DBConnection[]>([])
    const [form, setForm] = useState({
        username: '',
        password: '',
        database: '',
        host: '',
        port: '',
        memo: '',
    })
    const [bulkFile, setBulkFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [search, setSearch] = useState('')

    // DB 연결 목록 불러오기
    useEffect(() => {
        fetch('http://localhost:8000/admin/dbconnections')
            .then((res) => res.json())
            .then((data) => setConnections(data.dbconnections))
    }, [])

    // 폼 제출 핸들러
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        const res = await fetch('http://localhost:8000/admin/add-dbconnection', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(form),
        })

        if (res.ok) {
            alert('추가 성공!')
            location.reload()
        } else {
            const err = await res.json()
            alert(`추가 실패: ${err.detail}`)
        }
    }

    const handleDelete = async (id: number) => {
        if (!confirm("정말 삭제하시겠습니까?")) return;
        const res = await fetch(`http://localhost:8000/admin/delete-dbconnection/${id}`, {
            method: 'DELETE',
        })

        if (res.ok) {
            alert('삭제 성공!');
            setConnections(connections.filter(conn => conn.id != id));
        } else {
            const err = await res.json();
            alert(`삭제 실패: ${err.detail}`)
        }
    }

    // 검색 필터
    const filtered = connections.filter(conn =>
        [conn.database, conn.host, conn.username, conn.port, conn.memo]
            .some(val =>
                String(val ?? '')
                    .toLowerCase()
                    .includes(search.toLowerCase())
            )
    )

    // 엑셀 업로드 핸들러
    const handleBulkFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setBulkFile(e.target.files[0]);
        }
    }
    const handleBulkUpload = async () => {
        if (!bulkFile) {
            alert('업로드할 파일을 선택하세요.');
            return;
        }
        const formData = new FormData();
        formData.append('file', bulkFile);

        const res = await fetch('http://localhost:8000/admin/bulk-upload-dbconnections', {
            method: 'POST',
            body: formData,
        })
        if (res.ok) {
            const data = await res.json();
            alert(data.msg + '\n' + (data.errors?.join('\n') || ''));
            location.reload();
        } else {
            const err = await res.json();
            alert('업로드 실패: ' + err.detail);
        }

        setBulkFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    }

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-6">📡 DB 연결 관리</h1>

            {/* 엑셀 업로드 */}
            <div className="mb-6">
                <label className="font-semibold">엑셀로 추가하기</label>
                <div className="flex items-center gap-2">
                    <input
                        type="file"
                        accept=".xlsx,.csv"
                        onChange={handleBulkFileChange}
                        ref={fileInputRef}
                        className="border p-2 rounded"
                    />
                    <button
                        onClick={handleBulkUpload}
                        className="bg-green-700 text-white p-2 rounded hover:bg-green-800"
                    >
                        업로드
                    </button>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                    username, password, database, host, port, memo<br/>
                    순서대로 엑셀파일에 입력 후 업로드
                </p>
            </div>

            {/* 좌우 배치: flex 사용 */}
            <div className="flex flex-col md:flex-row gap-6 items-start">
                {/* ─ 왼쪽 : DB 추가 폼 ─ */}
                <div className="md:w-1/2">
                    <h2 className="text-xl font-semibold mb-2 mt-0">➕ DB 연결 추가</h2>
                    <form onSubmit={handleSubmit} className="grid gap-2">
                        {['username', 'password', 'database', 'host', 'port', 'memo'].map(key => (
                            <input
                                key={key}
                                name={key}
                                placeholder={key}
                                className="border p-2 rounded"
                                value={(form as any)[key]}
                                onChange={e => setForm({...form, [key]: e.target.value})}
                                required={key !== 'memo'}
                            />
                        ))}
                        <button className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700">
                            추가하기
                        </button>
                    </form>
                </div>

                {/* ─ 오른쪽 : 검색 + 연결 목록 ─ */}
                <div className="md:w-1/2 flex flex-col gap-2 self-start -mt-2">
                    {/* 검색창 */}
                    <input
                        type="text"
                        placeholder="검색어 (DB명, 주소, 유저, 포트, 메모)"
                        className="border px-3 py-2 rounded w-full md:w-96 mt-0"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />

                    {/* 목록 제목 */}
                    <h2 className="text-xl font-semibold mb-2 mt-0">📋 연결 목록</h2>

                    {/* 테이블 */}
                    <div className="overflow-x-auto max-h-[500px] overflow-y-auto border rounded">
                        <table className="min-w-full text-sm text-left text-gray-200">
                            <thead className="bg-gray-700 text-white sticky top-0">
                            <tr>
                                <th className="px-4 py-2">DB 이름</th>
                                <th className="px-4 py-2">주소</th>
                                <th className="px-4 py-2">유저</th>
                                <th className="px-4 py-2">포트</th>
                                <th className="px-4 py-2">메모</th>
                                <th className="px-4 py-2">삭제</th>
                            </tr>
                            </thead>
                            <tbody className="bg-gray-800">
                            {filtered.map(conn => (
                                <tr key={conn.id} className="border-b border-gray-600 hover:bg-gray-700">
                                    <td className="px-4 py-2">{conn.database}</td>
                                    <td className="px-4 py-2">{conn.host}</td>
                                    <td className="px-4 py-2">{conn.username}</td>
                                    <td className="px-4 py-2">{conn.port}</td>
                                    <td className="px-4 py-2">{conn.memo}</td>
                                    <td className="px-4 py-2">
                                        <button
                                            onClick={() => handleDelete(conn.id)}
                                            className="text-red-400 hover:text-red-600"
                                        >
                                            삭제
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {filtered.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="text-center text-gray-400 py-4">
                                        검색 결과가 없습니다.
                                    </td>
                                </tr>
                            )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    )

}
