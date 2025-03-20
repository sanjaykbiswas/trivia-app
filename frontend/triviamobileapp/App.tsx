import React from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import WelcomeScreen from './src/screens/WelcomeScreen';

function App(): React.JSX.Element {
  return (
    <SafeAreaView style={styles.container}>
      <WelcomeScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default App;