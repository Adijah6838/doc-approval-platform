import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem('token');
  const headers = { Authorization: 'Bearer ' + token };

  useEffect(() => {
    if (!token) return;
    axios.get('http://localhost:8000/auth/me', { headers })
      .then(res => setUser(res.data))
      .catch(err => console.error(err));

    fetchDocuments();
  }, [token]);

  const fetchDocuments = () => {
    setLoading(true);
    axios.get('http://localhost:8000/documents/', { headers })
      .then(res => setDocuments(res.data.items))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !title) return;

    const formData = new FormData();
    formData.append('title', title);
    formData.append('file', file);

    try {
      await axios.post('http://localhost:8000/documents/upload', formData, { headers });
      setTitle('');
      setFile(null);
      fetchDocuments();
    } catch (err) {
      alert('Upload failed!');
    }
  };

  const handleStatusChange = async (docId, newStatus) => {
    try {
      await axios.patch('http://localhost:8000/documents/' + docId + '/status?new_status=' + newStatus, {}, { headers });
      fetchDocuments();
    } catch (err) {
      alert('Failed to update status. You might not have permission.');
    }
  };

  const handleDownload = async (docId, fileName) => {
    try {
      const response = await axios.get('http://localhost:8000/documents/' + docId + '/download', {
        headers,
        responseType: 'blob' // Tell axios to expect a file
      });
      
      // Create a fake link to trigger the browser download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName || 'document');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Download failed.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  if (!user) return <div style={{ padding: '40px' }}>Loading...</div>;

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', backgroundColor: '#f9fafb', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <div>
          <h1 style={{ margin: 0 }}>Document Dashboard</h1>
          <p style={{ margin: '5px 0 0 0', color: '#666' }}>Logged in as {user.email} ({user.role})</p>
        </div>
        <button onClick={handleLogout} style={{ padding: '10px 20px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Logout
        </button>
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '30px' }}>
        <h3>Upload New Document</h3>
        <form onSubmit={handleUpload} style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <input type='text' placeholder='Document Title' value={title} onChange={e => setTitle(e.target.value)} style={{ padding: '10px', border: '1px solid #ccc', borderRadius: '4px', flex: 1 }} required />
          <input type='file' onChange={e => setFile(e.target.files[0])} style={{ flex: 1 }} required />
          <button type='submit' style={{ padding: '10px 20px', backgroundColor: '#2563eb', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Upload</button>
        </form>
      </div>

      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead style={{ backgroundColor: '#f3f4f6' }}>
            <tr>
              <th style={{ padding: '15px', borderBottom: '1px solid #e5e7eb' }}>ID</th>
              <th style={{ padding: '15px', borderBottom: '1px solid #e5e7eb' }}>Title</th>
              <th style={{ padding: '15px', borderBottom: '1px solid #e5e7eb' }}>Status</th>
              <th style={{ padding: '15px', borderBottom: '1px solid #e5e7eb' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan='4' style={{ padding: '20px', textAlign: 'center' }}>Loading documents...</td></tr>
            ) : documents.length === 0 ? (
              <tr><td colSpan='4' style={{ padding: '20px', textAlign: 'center' }}>No documents found.</td></tr>
            ) : (
              documents.map(doc => (
                <tr key={doc.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '15px' }}>{doc.id}</td>
                  <td style={{ padding: '15px', fontWeight: 'bold' }}>{doc.title}</td>
                  <td style={{ padding: '15px' }}>
                    <span style={{ 
                      padding: '5px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold',
                      backgroundColor: doc.status === 'approved' ? '#d1fae5' : doc.status === 'rejected' ? '#fee2e2' : doc.status === 'pending' ? '#fef3c7' : '#e5e7eb',
                      color: doc.status === 'approved' ? '#065f46' : doc.status === 'rejected' ? '#991b1b' : doc.status === 'pending' ? '#92400e' : '#374151'
                    }}>
                      {doc.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '15px', display: 'flex', gap: '10px' }}>
                    {doc.versions && doc.versions.length > 0 && (
                      <button onClick={() => handleDownload(doc.id, doc.versions[0].file_name)} style={{ padding: '5px 10px', backgroundColor: '#6b7280', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Download</button>
                    )}
                    {doc.status !== 'approved' && (
                      <button onClick={() => handleStatusChange(doc.id, 'approved')} style={{ padding: '5px 10px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Approve</button>
                    )}
                    {doc.status !== 'rejected' && (
                      <button onClick={() => handleStatusChange(doc.id, 'rejected')} style={{ padding: '5px 10px', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Reject</button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}