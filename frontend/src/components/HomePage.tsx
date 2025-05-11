import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import Navbar from './Navbar';

const HomePage = () => {
    return (
        <div className="flex flex-col w-full h-screen text-[#F5F5F5]">
            <Navbar />
            <div className="flex-grow flex items-center justify-center">
                <h1 className="text-[#1E3A8A] text-4xl font-bold text-center">Welcome to my mini CI-CD pipeline project</h1>
            </div>
        </div>
    );
};

export default HomePage;