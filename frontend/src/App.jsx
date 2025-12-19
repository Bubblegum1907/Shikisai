import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import Callback from "./pages/callback";
import Recommendations from "./pages/recommendations";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/callback" element={<Callback />} />
        <Route path="/recommendations" element={<Recommendations />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
