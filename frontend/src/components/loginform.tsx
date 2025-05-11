import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../auth/authservice';
import type { LoginRequest } from '../types/types';

const LoginForm = () => {
    const [form, setForm] = useState<LoginRequest>({
        email: '',
        password: '',
    });
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const cookies = document.cookie.split('; ').find(row => row.startsWith('token='));
        if (cookies) {
            navigate('/');
        }
    }, [navigate]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setForm({ ...form, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const data = await loginUser(form);
            document.cookie = `token=${data.access_token}; path=/; SameSite=Lax; Secure`;
            navigate('/');
        } catch (err: any) {
            setError(err.response.data.detail.toString());
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
                <form
                        onSubmit={handleSubmit}
                        className="w-full max-w-sm p-6 bg-white rounded-lg shadow-md"
                >
                        <h2 className="mb-6 text-2xl font-bold text-center text-blue-600">
                                Login
                        </h2>
                        {error && (
                                <div className="mb-4 text-sm text-red-600">
                                        {error}
                                </div>
                        )}
                        <div className="mb-4">
                                <label
                                        htmlFor="email"
                                        className="block mb-2 text-sm font-medium text-gray-700"
                                >
                                        Email
                                </label>
                                <input
                                        type="email"
                                        id="email"
                                        name="email"
                                        value={form.email}
                                        onChange={handleChange}
                                        className="w-full px-3 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring focus:ring-blue-300"
                                        required
                                />
                        </div>
                        <div className="mb-6">
                                <label
                                        htmlFor="password"
                                        className="block mb-2 text-sm font-medium text-gray-700"
                                >
                                        Password
                                </label>
                                <input
                                        type="password"
                                        id="password"
                                        name="password"
                                        value={form.password}
                                        onChange={handleChange}
                                        className="w-full px-3 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring focus:ring-blue-300"
                                        required
                                />
                        </div>
                        <button
                                type="submit"
                                className="w-full px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring focus:ring-blue-300"
                        >
                                Login
                        </button>
                </form>
        </div>
    );
};

export default LoginForm;