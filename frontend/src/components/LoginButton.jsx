export default function LoginButton() {
  const handleLogin = () => {
    window.location.href = "http://127.0.0.1:8000/auth/login";
  };

  return (
    <button
      onClick={handleLogin}
      style={{
        padding: "12px 28px",
        borderRadius: "999px",
        fontSize: "0.95rem",
        fontWeight: 600,
        background: "linear-gradient(135deg, #E7FFF3, #E0E7FF)",
        color: "#4F5BD5",
        cursor: "pointer",
      }}
    >
      Connect with Spotify
    </button>
  );
}
