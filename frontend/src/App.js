import React, { useEffect, useMemo, useState } from 'react';
import './App.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api';

function getStoredToken() {
	try { return localStorage.getItem('token') || ''; } catch { return ''; }
}
function setStoredToken(token) {
	try { localStorage.setItem('token', token || ''); } catch {}
}

async function apiFetch(path, { method = 'GET', headers = {}, body, token } = {}) {
	const url = `${API_BASE}${path}`;
	const finalHeaders = { ...headers };
	if (token) finalHeaders['Authorization'] = `Token ${token}`;
	const res = await fetch(url, { method, headers: finalHeaders, body });
	if (res.status === 204) return null;
	const data = await res.json().catch(() => ({}));
	if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
	return data;
}

function useAuth() {
	const [token, setToken] = useState(getStoredToken());
	const [user, setUser] = useState(null);
	useEffect(() => {
		if (!token) { setUser(null); return; }
		apiFetch('/auth/me/', { token }).then(setUser).catch(() => setUser(null));
	}, [token]);
	const login = async (username, password) => {
		const data = await apiFetch('/auth/token/', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ username, password })
		});
		setToken(data.token);
		setStoredToken(data.token);
	};
	const logout = () => { setToken(''); setStoredToken(''); setUser(null); };
	return { token, user, login, logout };
}

function Section({ title, children, actions }) {
	return (
		<div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 8, marginBottom: 16 }}>
			<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
				<h3 style={{ margin: 0 }}>{title}</h3>
				{actions}
			</div>
			{children}
		</div>
	);
}

function LoginPanel({ auth }) {
	const [username, setUsername] = useState('admin');
	const [password, setPassword] = useState('adminpass');
	const [err, setErr] = useState('');
	const [loading, setLoading] = useState(false);
	const onSubmit = async (e) => {
		e.preventDefault();
		setErr(''); setLoading(true);
		try { await auth.login(username, password); } catch (e) { setErr(String(e.message || e)); } finally { setLoading(false); }
	};
	if (auth.user) {
		return (
			<div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
				<span>Signed in as <strong>{auth.user.username}</strong></span>
				<button onClick={auth.logout}>Logout</button>
			</div>
		);
	}
	return (
		<form onSubmit={onSubmit} style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
			<input value={username} onChange={e => setUsername(e.target.value)} placeholder="username" />
			<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="password" />
			<button type="submit" disabled={loading}>{loading ? '...' : 'Login'}</button>
			{err && <span style={{ color: 'crimson' }}>{err}</span>}
		</form>
	);
}

function Taxonomy({ auth }) {
	const [subjects, setSubjects] = useState([]);
	const [topics, setTopics] = useState([]);
	const [chapters, setChapters] = useState([]);
	const fetchAll = async () => {
		const [subs, tops, chaps] = await Promise.all([
			apiFetch('/subjects/'), apiFetch('/topics/'), apiFetch('/chapters/')
		]);
		setSubjects(subs); setTopics(tops); setChapters(chaps);
	};
	useEffect(() => { fetchAll(); }, []);

	const [newSubject, setNewSubject] = useState('');
	const [newTopic, setNewTopic] = useState({ subject: '', name: '' });
	const [newChapter, setNewChapter] = useState({ topic: '', title: '' });

	const createSubject = async () => {
		if (!newSubject) return;
		await apiFetch('/subjects/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newSubject }), token: auth.token });
		setNewSubject('');
		fetchAll();
	};
	const createTopic = async () => {
		if (!newTopic.subject || !newTopic.name) return;
		await apiFetch('/topics/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newTopic), token: auth.token });
		setNewTopic({ subject: '', name: '' });
		fetchAll();
	};
	const createChapter = async () => {
		if (!newChapter.topic || !newChapter.title) return;
		await apiFetch('/chapters/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newChapter), token: auth.token });
		setNewChapter({ topic: '', title: '' });
		fetchAll();
	};

	return (
		<div>
			<Section title="Subjects">
				<ul>
					{subjects.map(s => <li key={s.id}>{s.id}. {s.name}</li>)}
				</ul>
				<div style={{ display: 'flex', gap: 8 }}>
					<input placeholder="New subject" value={newSubject} onChange={e => setNewSubject(e.target.value)} />
					<button onClick={createSubject} disabled={!auth.token}>Add</button>
				</div>
			</Section>
			<Section title="Topics">
				<ul>
					{topics.map(t => <li key={t.id}>{t.id}. subj {t.subject} - {t.name}</li>)}
				</ul>
				<div style={{ display: 'flex', gap: 8 }}>
					<input placeholder="Subject ID" value={newTopic.subject} onChange={e => setNewTopic(v => ({ ...v, subject: e.target.value }))} />
					<input placeholder="Topic name" value={newTopic.name} onChange={e => setNewTopic(v => ({ ...v, name: e.target.value }))} />
					<button onClick={createTopic} disabled={!auth.token}>Add</button>
				</div>
			</Section>
			<Section title="Chapters">
				<ul>
					{chapters.map(c => <li key={c.id}>{c.id}. topic {c.topic} - {c.title}</li>)}
				</ul>
				<div style={{ display: 'flex', gap: 8 }}>
					<input placeholder="Topic ID" value={newChapter.topic} onChange={e => setNewChapter(v => ({ ...v, topic: e.target.value }))} />
					<input placeholder="Chapter title" value={newChapter.title} onChange={e => setNewChapter(v => ({ ...v, title: e.target.value }))} />
					<button onClick={createChapter} disabled={!auth.token}>Add</button>
				</div>
			</Section>
		</div>
	);
}

function Resources({ auth }) {
	const [items, setItems] = useState([]);
	const [loading, setLoading] = useState(true);
	const [q, setQ] = useState('');
	const load = async () => {
		setLoading(true);
		const data = await apiFetch(`/resources/?q=${encodeURIComponent(q)}`);
		setItems(data); setLoading(false);
	};
	useEffect(() => { load(); }, []);

	const [form, setForm] = useState({ title: '', description: '', subject: '', topic: '', chapter: '', difficulty: 'medium', tags: '' });
	const [file, setFile] = useState(null);
	const createResource = async () => {
		const fd = new FormData();
		Object.entries(form).forEach(([k, v]) => v && fd.append(k, v));
		if (file) fd.append('file', file);
		await apiFetch('/resources/', { method: 'POST', body: fd, token: auth.token });
		setForm({ title: '', description: '', subject: '', topic: '', chapter: '', difficulty: 'medium', tags: '' }); setFile(null);
		load();
	};
	const uploadVersion = async (resourceId, file) => {
		const fd = new FormData();
		fd.append('file', file);
		await apiFetch(`/resources/${resourceId}/upload_version/`, { method: 'POST', body: fd, token: auth.token });
		load();
	};

	return (
		<div>
			<div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
				<input placeholder="Search in resources" value={q} onChange={e => setQ(e.target.value)} />
				<button onClick={load}>Search</button>
			</div>
			<Section title="Create Resource">
				<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
					<input placeholder="Title" value={form.title} onChange={e => setForm(v => ({ ...v, title: e.target.value }))} />
					<input placeholder="Description" value={form.description} onChange={e => setForm(v => ({ ...v, description: e.target.value }))} />
					<input placeholder="Subject ID (optional)" value={form.subject} onChange={e => setForm(v => ({ ...v, subject: e.target.value }))} />
					<input placeholder="Topic ID (optional)" value={form.topic} onChange={e => setForm(v => ({ ...v, topic: e.target.value }))} />
					<input placeholder="Chapter ID (optional)" value={form.chapter} onChange={e => setForm(v => ({ ...v, chapter: e.target.value }))} />
					<select value={form.difficulty} onChange={e => setForm(v => ({ ...v, difficulty: e.target.value }))}>
						<option value="easy">easy</option>
						<option value="medium">medium</option>
						<option value="hard">hard</option>
					</select>
					<input placeholder="tags (comma)" value={form.tags} onChange={e => setForm(v => ({ ...v, tags: e.target.value }))} />
					<input type="file" onChange={e => setFile(e.target.files?.[0] || null)} />
					<button onClick={createResource} disabled={!auth.token}>Create</button>
				</div>
			</Section>
			{loading ? <p>Loading...</p> : (
				<ul>
					{items.map(r => (
						<li key={r.id} style={{ marginBottom: 8 }}>
							<div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
								<strong>{r.title}</strong> — {r.description}
								{r.versions?.[0]?.file && (
									<a href={r.versions[0].file} target="_blank" rel="noreferrer" style={{ marginLeft: 8 }}>Download latest</a>
								)}
								{auth.token && (
									<label style={{ marginLeft: 8 }}>
										<span>New version</span>
										<input type="file" style={{ marginLeft: 6 }} onChange={e => e.target.files?.[0] && uploadVersion(r.id, e.target.files[0])} />
									</label>
								)}
							</div>
						</li>
					))}
				</ul>
			)}
		</div>
	);
}

function SearchAll() {
	const [q, setQ] = useState('');
	const [res, setRes] = useState(null);
	const search = async () => {
		const data = await apiFetch(`/search/?q=${encodeURIComponent(q)}`);
		setRes(data);
	};
	return (
		<div>
			<div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
				<input placeholder="Search everything" value={q} onChange={e => setQ(e.target.value)} />
				<button onClick={search}>Go</button>
			</div>
			{res && (
				<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
					<Section title={`Resources (${res.resources.length})`}>
						<ul>
							{res.resources.map(r => <li key={r.id}>{r.title}</li>)}
						</ul>
					</Section>
					<Section title={`Quizzes (${res.quizzes.length})`}>
						<ul>
							{res.quizzes.map(qz => <li key={qz.id}>{qz.title}</li>)}
						</ul>
					</Section>
				</div>
			)}
		</div>
	);
}

function Quizzes({ auth }) {
	const [quizzes, setQuizzes] = useState([]);
	const [selected, setSelected] = useState(null);
	const [questions, setQuestions] = useState([]);
	const [answers, setAnswers] = useState({});
	const load = async () => { setQuizzes(await apiFetch('/quizzes/')); };
	useEffect(() => { load(); }, []);
	const takeQuiz = async (q) => {
		setSelected(q); setAnswers({});
		const qs = await apiFetch(`/quizzes/${q.id}/take/`);
		setQuestions(qs);
	};
	const submit = async () => {
		if (!auth.user) return;
		const payload = {
			student: auth.user.id,
			answers: questions.map(q => ({
				question: q.id,
				selected_choice: answers[q.id] || null,
				text_answer: ''
			}))
		};
		const res = await apiFetch(`/quizzes/${selected.id}/grade/`, {
			method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), token: auth.token
		});
		alert(`Score: ${res.score.toFixed(2)}%`);
	};
	return (
		<div>
			<ul>
				{quizzes.map(q => (
					<li key={q.id} style={{ marginBottom: 8 }}>
						{q.title}
						<button style={{ marginLeft: 8 }} onClick={() => takeQuiz(q)}>Take</button>
					</li>
				))}
			</ul>
			{selected && (
				<Section title={`Taking: ${selected.title}`}>
					{questions.map(q => (
						<div key={q.id} style={{ marginBottom: 12 }}>
							<div style={{ fontWeight: 'bold' }}>{q.text}</div>
							{q.choices?.map(c => (
								<label key={c.id} style={{ display: 'block' }}>
									<input type="radio" name={`q${q.id}`} checked={answers[q.id] === c.id} onChange={() => setAnswers(v => ({ ...v, [q.id]: c.id }))} /> {c.text}
								</label>
							))}
						</div>
					))}
					{auth.token && <button onClick={submit}>Submit</button>}
				</Section>
			)}
		</div>
	);
}

function Dashboard({ auth }) {
	const [data, setData] = useState(null);
	useEffect(() => { if (auth.token) apiFetch('/dashboard/', { token: auth.token }).then(setData); }, [auth.token]);
	if (!auth.token) return <p>Login to view your dashboard.</p>;
	if (!data) return <p>Loading...</p>;
	return (
		<div>
			<p>Average score: <strong>{Number(data.avg_score).toFixed(2)}%</strong></p>
			<p>Attempts: {data.num_attempts}</p>
			<Section title="By Subject">
				<ul>
					{data.subjects.map(s => <li key={s.quiz__subject__name || 'none'}>{s.quiz__subject__name || 'Uncategorized'}: {Number(s.avg).toFixed(2)}%</li>)}
				</ul>
			</Section>
		</div>
	);
}

function Homework({ auth }) {
	const [items, setItems] = useState([]);
	const [title, setTitle] = useState('');
	const [desc, setDesc] = useState('');
	const [due, setDue] = useState('');
	const [file, setFile] = useState(null);
	const load = async () => setItems(await apiFetch('/homeworks/'));
	useEffect(() => { load(); }, []);
	const create = async () => {
		if (!auth.token) return;
		await apiFetch('/homeworks/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, description: desc, due_date: due }), token: auth.token });
		setTitle(''); setDesc(''); setDue(''); load();
	};
	const submitTo = async (homeworkId, text) => {
		if (!auth.user) return;
		const fd = new FormData();
		fd.append('homework', homeworkId);
		fd.append('student', auth.user.id);
		fd.append('text_response', text);
		if (file) fd.append('file', file);
		await apiFetch('/submissions/', { method: 'POST', body: fd, token: auth.token });
		alert('Submitted');
	};
	return (
		<div>
			<Section title="Create Homework">
				<div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
					<input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} />
					<input placeholder="Description" value={desc} onChange={e => setDesc(e.target.value)} />
					<input type="datetime-local" value={due} onChange={e => setDue(e.target.value)} />
					<button onClick={create} disabled={!auth.token}>Add</button>
				</div>
			</Section>
			<ul>
				{items.map(h => (
					<li key={h.id} style={{ marginBottom: 8 }}>
						<strong>{h.title}</strong> — due {new Date(h.due_date).toLocaleString()}
						<div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
							<input placeholder="Your answer" id={`ans-${h.id}`} />
							<input type="file" onChange={e => setFile(e.target.files?.[0] || null)} />
							<button onClick={() => submitTo(h.id, document.getElementById(`ans-${h.id}`).value)} disabled={!auth.token}>Submit</button>
						</div>
					</li>
				))}
			</ul>
		</div>
	);
}

function Bookmarks({ auth }) {
	const [bookmarks, setBookmarks] = useState([]);
	const load = async () => { if (auth.token) setBookmarks(await apiFetch('/bookmarks/', { token: auth.token })); };
	useEffect(() => { load(); }, [auth.token]);
	const addForResource = async (resourceId) => {
		await apiFetch('/bookmarks/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resource: resourceId, user: auth.user.id }), token: auth.token });
		load();
	};
	const remove = async (id) => { await apiFetch(`/bookmarks/${id}/`, { method: 'DELETE', token: auth.token }); load(); };
	return (
		<div>
			<p>Use the Resources tab to create resources. You can add bookmarks here by resource ID.</p>
			<div style={{ display: 'flex', gap: 6 }}>
				<input id="bm-res" placeholder="Resource ID" />
				<button onClick={() => addForResource(Number(document.getElementById('bm-res').value))} disabled={!auth.token}>Bookmark</button>
			</div>
			<ul>
				{bookmarks.map(b => (
					<li key={b.id}>#{b.id} resource {b.resource || '-'} quiz {b.quiz || '-'} <button onClick={() => remove(b.id)}>Remove</button></li>
				))}
			</ul>
		</div>
	);
}

function Notifications({ auth }) {
	const [notifications, setNotifications] = useState([]);
	const load = async () => { if (auth.token) setNotifications(await apiFetch('/notifications/', { token: auth.token })); };
	useEffect(() => { load(); }, [auth.token]);
	const mark = async (id) => { await apiFetch(`/notifications/${id}/mark_read/`, { method: 'POST', token: auth.token }); load(); };
	return (
		<div>
			<ul>
				{notifications.map(n => (
					<li key={n.id}>
						{n.is_read ? '✓' : '•'} <strong>{n.title}:</strong> {n.body} {(!n.is_read) && <button onClick={() => mark(n.id)}>Mark read</button>}
					</li>
				))}
			</ul>
		</div>
	);
}

function Progress({ auth }) {
	const [topics, setTopics] = useState([]);
	const load = async () => setTopics(await apiFetch('/topics/'));
	useEffect(() => { load(); }, []);
	const complete = async (topicId) => { await apiFetch('/progress/mark_complete/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic: topicId }), token: auth.token }); alert('Marked complete'); };
	return (
		<div>
			<ul>
				{topics.map(t => (
					<li key={t.id}>#{t.id} {t.name} <button onClick={() => complete(t.id)} disabled={!auth.token}>Complete</button></li>
				))}
			</ul>
		</div>
	);
}

function AIGenerator({ auth }) {
	const [text, setText] = useState('');
	const [file, setFile] = useState(null);
	const [generated, setGenerated] = useState([]);
	const [title, setTitle] = useState('AI Generated Quiz');
	const generate = async () => {
		if (!text && !file) return;
		let body; let headers = {};
		if (file) { const fd = new FormData(); if (text) fd.append('text', text); fd.append('file', file); body = fd; }
		else { body = JSON.stringify({ text }); headers['Content-Type'] = 'application/json'; }
		const res = await apiFetch('/ai/generate-questions/', { method: 'POST', body, headers, token: auth.token });
		setGenerated(res.questions || []);
	};
	const createQuiz = async () => {
		if (!auth.token) return;
		const payload = { title, questions: generated };
		await apiFetch('/quizzes/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), token: auth.token });
		alert('Quiz created');
	};
	return (
		<div>
			<div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
				<textarea placeholder="Paste study text" value={text} onChange={e => setText(e.target.value)} style={{ width: 400, height: 120 }} />
				<div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
					<input type="file" onChange={e => setFile(e.target.files?.[0] || null)} />
					<button onClick={generate} disabled={!auth.token}>Generate Questions</button>
					<input placeholder="Quiz title" value={title} onChange={e => setTitle(e.target.value)} />
					<button onClick={createQuiz} disabled={!auth.token || generated.length === 0}>Create Quiz</button>
				</div>
			</div>
			{generated.length > 0 && (
				<Section title="Preview">
					<ol>
						{generated.map((q, idx) => (
							<li key={idx}>
								<div>{q.text}</div>
								<ul>
									{q.choices.map((c, i) => <li key={i}>{c.text}{c.is_correct ? ' (correct)' : ''}</li>)}
								</ul>
							</li>
						))}
					</ol>
				</Section>
			)}
		</div>
	);
}

function AIChat() {
	const [question, setQuestion] = useState('What is photosynthesis?');
	const [answer, setAnswer] = useState('');
	const ask = async () => {
		const res = await apiFetch('/ai/chat/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) });
		setAnswer(`${res.answer}${res.resource_title ? `\nSource: ${res.resource_title}` : ''}`);
	};
	return (
		<Section title="AI Study Assistant">
			<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
				<input style={{ flex: 1 }} value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask about your materials" />
				<button onClick={ask}>Ask</button>
			</div>
			{answer && (
				<pre style={{ marginTop: 8, whiteSpace: 'pre-wrap', textAlign: 'left' }}>{answer}</pre>
			)}
		</Section>
	);
}

function App() {
	const auth = useAuth();
	const [tab, setTab] = useState('resources');
	const tabs = useMemo(() => ([
		{ id: 'resources', label: 'Resources', render: () => <Resources auth={auth} /> },
		{ id: 'search', label: 'Search', render: () => <SearchAll /> },
		{ id: 'quizzes', label: 'Quizzes', render: () => <Quizzes auth={auth} /> },
		{ id: 'dashboard', label: 'Dashboard', render: () => <Dashboard auth={auth} /> },
		{ id: 'homework', label: 'Homework', render: () => <Homework auth={auth} /> },
		{ id: 'bookmarks', label: 'Bookmarks', render: () => <Bookmarks auth={auth} /> },
		{ id: 'notifications', label: 'Notifications', render: () => <Notifications auth={auth} /> },
		{ id: 'progress', label: 'Progress', render: () => <Progress auth={auth} /> },
		{ id: 'ai', label: 'AI Generator', render: () => <AIGenerator auth={auth} /> },
		{ id: 'chat', label: 'AI Chat', render: () => <AIChat /> },
		{ id: 'taxonomy', label: 'Subjects/Topics', render: () => <Taxonomy auth={auth} /> },
	]), [auth]);
	return (
		<div className="App" style={{ padding: 16 }}>
			<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
				<h2 style={{ margin: 0 }}>EduSuite LMS</h2>
				<LoginPanel auth={auth} />
			</div>
			<div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
				{tabs.map(t => (
					<button key={t.id} onClick={() => setTab(t.id)} disabled={tab === t.id}>{t.label}</button>
				))}
			</div>
			{tabs.find(t => t.id === tab)?.render()}
			<p style={{ marginTop: 24, color: '#666' }}>Backend: {API_BASE} — set REACT_APP_API_BASE to override</p>
		</div>
	);
}

export default App;
