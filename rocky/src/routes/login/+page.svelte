

<div class="background">
  <div class="card">
    <div class="header">
      <img src="/ksu_horizontal.png" alt="Kent State University" class="logo" />
      <img src="/rock.jpg" alt="Rocky Logo" class="logo-rock" />
      <h2>Rocky AI</h2>
      <p class="subtitle">Kent State University</p>
    </div>

    <h1>Sign in to Rocky</h1>

    <button class="signin" >
      Sign In
    </button>
  </div>
</div>

    <!-- CSS -->

<style>
  .background {
    min-height: 100vh;
    display: grid;
    place-items: center;

    background-image: url("/commencement_dark.jpg");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
  }

  .card {
    width: 100%;
    max-width: 500px;
    background: white;
    border-radius: 6px;
    padding: 40px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    text-align: center;
  }

  .header {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .header h2 {
    margin: 0;
    font-size: 28px;
    font-weight: 700;
    color: #003976;
    font-family: "National", "Soho", "ui-sans-serif", "system-ui";
  }

  .logo {
    width: 200px;
    margin-bottom: 20px;
  }

  .logo-rock {
    width: 100px;
    margin-bottom: 10px;
  }

  .subtitle {
    margin-top: 4px;
    color: #555;
    font-size: 14px;
  }

  h1 {
    margin: 30px 0 20px;
    font-weight: 500;
  }

  .signin {
    background-color: #005bbb; /* school-style blue */
    color: white;
    border: none;
    padding: 14px 30px;
    font-size: 18px;
    border-radius: 4px;
    cursor: pointer;
  }

  .signin:hover {
    background-color: #004a99;
  }
</style>
