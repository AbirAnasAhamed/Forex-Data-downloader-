// Web Crypto API utility for secure local storage
// Hedge Fund Standard: Encrypting tokens at rest in the browser

const ENCRYPTION_KEY = "Forex-Advanced-Pipeline-Secure-Key-2026"; // In production, this might be fetched dynamically or obfuscated

async function getDerivedKey(salt: Uint8Array): Promise<CryptoKey> {
    const encoder = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
        "raw",
        encoder.encode(ENCRYPTION_KEY),
        { name: "PBKDF2" },
        false,
        ["deriveBits", "deriveKey"]
    );
    return window.crypto.subtle.deriveKey(
        {
            name: "PBKDF2",
            salt: salt as any,
            iterations: 100000,
            hash: "SHA-256"
        },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        false,
        ["encrypt", "decrypt"]
    );
}

export async function secureStore(key: string, value: string): Promise<void> {
    try {
        const salt = window.crypto.getRandomValues(new Uint8Array(16));
        const iv = window.crypto.getRandomValues(new Uint8Array(12));
        const derivedKey = await getDerivedKey(salt);
        
        const encoder = new TextEncoder();
        const encryptedContent = await window.crypto.subtle.encrypt(
            { name: "AES-GCM", iv: iv },
            derivedKey,
            encoder.encode(value)
        );

        const encryptedArray = Array.from(new Uint8Array(encryptedContent));
        const saltArray = Array.from(salt);
        const ivArray = Array.from(iv);

        const storageObject = {
            s: btoa(String.fromCharCode.apply(null, saltArray)),
            i: btoa(String.fromCharCode.apply(null, ivArray)),
            c: btoa(String.fromCharCode.apply(null, encryptedArray))
        };

        localStorage.setItem(`secure_${key}`, JSON.stringify(storageObject));
    } catch (e) {
        console.error("Encryption failed:", e);
    }
}

export async function secureRetrieve(key: string): Promise<string | null> {
    try {
        const stored = localStorage.getItem(`secure_${key}`);
        if (!stored) return null;

        const storageObject = JSON.parse(stored);
        
        const saltArray = Uint8Array.from(atob(storageObject.s), c => c.charCodeAt(0));
        const ivArray = Uint8Array.from(atob(storageObject.i), c => c.charCodeAt(0));
        const encryptedArray = Uint8Array.from(atob(storageObject.c), c => c.charCodeAt(0));

        const derivedKey = await getDerivedKey(saltArray);
        
        const decryptedContent = await window.crypto.subtle.decrypt(
            { name: "AES-GCM", iv: ivArray },
            derivedKey,
            encryptedArray
        );

        const decoder = new TextDecoder();
        return decoder.decode(decryptedContent);
    } catch (e) {
        console.error("Decryption failed:", e);
        return null;
    }
}

export function secureRemove(key: string): void {
    localStorage.removeItem(`secure_${key}`);
}

// Authenticated Fetch Wrapper
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = await secureRetrieve('access_token');
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    return fetch(url, { ...options, headers });
}

// Get Auth Token specifically for WebSockets
export async function getWsToken(): Promise<string> {
    return (await secureRetrieve('access_token')) || '';
}

