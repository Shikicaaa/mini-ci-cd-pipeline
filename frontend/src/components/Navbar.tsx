import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const Navbar = () => {
  const { username, logout } = useAuth();
  console.log(username);
  console.log(username ? username : "No user logged in");
  return (
    <nav className="bg-[#1E3A8A] p-4 flex justify-between items-center">
      <div className="text-white text-lg font-bold">
        <a className="text-white! font-bold! p-2 hover:text-blue-400!" href="/">
          CI-CD PIPELINE
        </a>
        <a className="text-white! font-bold! p-4 hover:text-blue-400!" href="https://github.com/apps/mini-ci-cd-pipeline">
          GET THE APP
        </a>
      </div>
      <div className="space-x-4">
        {username ? (
          <>
            <span className="text-[#F5F5F5] font-semibold">{username}</span>
            <Link to="/dashboard">
              <button className="bg-[#3B82F6] text-[#F5F5F5] px-4 py-2 rounded hover:bg-[#2563EB]">
                Dashboard
              </button>
            </Link>
            <button
              onClick={logout}
              className="bg-[#3B82F6] text-[#F5F5F5] px-4 py-2 rounded hover:bg-[#2563EB]"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login">
              <button className="bg-[#3B82F6] text-[#F5F5F5] px-4 py-2 rounded hover:bg-[#2563EB]">
                Login
              </button>
            </Link>
            <Link to="/register">
              <button className="bg-[#3B82F6] text-[#F5F5F5] px-4 py-2 rounded hover:bg-[#2563EB]">
                Register
              </button>
            </Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
