import { login } from "../api_call";
import { GOOGLE_CLIENT_APP_ID } from "../config";
import { Credentials } from "../credentials";
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';

type LoginButtonProps = {
    credentials : Credentials, 
    setCredentials : (a : Credentials)=>void,
}

function setToken(cvalue : string) {
    const cname = "token";
    const exdays = 30;
    const d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
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
                    const token = credentialResponse.credential;
                    if (token) {
                        const newCredential = {token : token, isSet : true};
                        login(newCredential).then((success)=>{
                            if (success) {
                                setCredentials(newCredential);
                                setToken(newCredential.token);
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