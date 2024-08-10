import { GOOGLE_CLIENT_APP_ID } from "../config";
import { Credentials } from "../credentials";
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';

type LoginButtonProps = {
    credentials : Credentials, 
    setCredentials : (a : Credentials)=>void,
}

export function LoginButton({
    credentials, setCredentials
} : LoginButtonProps) {
    if (!GOOGLE_CLIENT_APP_ID)
        throw new Error("[FATAL ERROR]: GOOGLE_CLIENT_APP_ID IS UNDEFINED")
    return <>
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_APP_ID}> 
            <GoogleLogin auto_select
                onSuccess={credentialResponse => {
                    if (credentialResponse.credential) {
                        setCredentials({token : credentialResponse.credential});
                        console.log("Login successful!")
                    }
                    else console.log("Login Failed");
                }}
                onError={() => {
                    console.log('Login Failed');
                }}
            />
        </GoogleOAuthProvider>
    </>
}