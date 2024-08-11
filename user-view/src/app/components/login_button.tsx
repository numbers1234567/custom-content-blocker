import { login } from "../api_call";
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

    // Login with a token
    function curatorLogin(token : string) {
        
    }

    return <>
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_APP_ID}> 
            <GoogleLogin auto_select
                onSuccess={credentialResponse => {
                    const token = credentialResponse.credential;
                    if (token) {
                        const newCredential = {token : token, isSet : true};
                        login(credentials).then((success)=>{
                            if (success) {
                                setCredentials(newCredential);
                                console.log("Login Successful");
                            }
                            else {
                                console.log("Login Failed. Server failed to authenticate.");
                            }
                        })
                    }
                    else console.log("Login Failed. Did not receive a valid token.");
                }}
                onError={() => {
                    console.log('Login Failed. Could not authenticate with Google.');
                }}
            />
        </GoogleOAuthProvider>
    </>
}