import { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";

export function useSocket(serverUrl: string = "http://localhost:8000") {
    const socketRef = useRef<Socket | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const socket = io(serverUrl, { autoConnect: false });
        socketRef.current = socket;

        socket.on("connect", () => setIsConnected(true));
        socket.on("disconnect", () => setIsConnected(false));

        return () => {
            socket.disconnect();
        };
    }, [serverUrl]);

    const connect = () => socketRef.current?.connect();
    const disconnect = () => socketRef.current?.disconnect();

    return { isConnected, connect, disconnect, socket: socketRef.current };
}
