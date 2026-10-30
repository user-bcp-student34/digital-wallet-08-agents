function fn() {
  var env = karate.env || 'local';
  karate.log('karate.env =', env);
  var config = {
    env: env,
    baseUrl: 'http://127.0.0.1:8000'
  };
  return config;
}
