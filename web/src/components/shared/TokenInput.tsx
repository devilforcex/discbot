import { useState } from "react";
import { useAuthStore } from "../../hooks/use-auth-store";
import Input from "../ui/Input";
import Button from "../ui/Button";

export default function TokenInput() {
  const { token, setToken } = useAuthStore();
  const [localToken, setLocalToken] = useState(token);
  const [show, setShow] = useState(false);

  const handleSave = () => {
    setToken(localToken);
  };

  return (
    <div className="flex flex-col gap-2">
      <Input
        label="API Token"
        type={show ? "text" : "password"}
        placeholder="Bearer token..."
        value={localToken}
        onChange={(e) => setLocalToken(e.target.value)}
      />
      <div className="flex gap-2">
        <Button variant="ghost" size="sm" onClick={() => setShow(!show)}>
          {show ? "Hide" : "Show"}
        </Button>
        <Button size="sm" onClick={handleSave}>
          Save
        </Button>
      </div>
    </div>
  );
}
